"""E3d grounding-decomposition environment and frozen prompt contracts.

E3d is a measurement-instrument qualification experiment.  It uses a targeted
evidence panel instead of complete coalition games and never exposes a future-query
or historical-test capability.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass
from itertools import product

from hibermem.backends.base import GenerationResult, LLMBackend
from hibermem.coalition.masks import mask_to_index
from hibermem.memory import MemoryItem

from .dataset import ControlledDataset, MemoryBank, Query, QuerySplit
from .factorial import SYSTEM_PROMPT as CURRENT_V1_SYSTEM_PROMPT


PROTOCOL = "phase2r-grounding-decomposition-v1"
DEVELOPMENT_ARMS = (
    "current_v1",
    "query_anchored_v1",
    "structured_verifier_v1",
)
VERIFICATION_ARMS = ("current_v1", "query_anchored_v1")
FAMILIES = ("and2", "and3")
OVERLAPS = ("low", "high")
WORLDS = ("base", "counterfactual")
LEDGER_MODES = ("single_path", "dual_path")

QUERY_ANCHORED_SYSTEM_PROMPT = (
    "Use only the supplied Link records. First extract the exact RQ start identifier "
    "named in the Task. Traverse only links reachable from that exact start and verify "
    "that every edge in a complete path to a DS destination is present. A complete path "
    "rooted at any other RQ identifier is irrelevant and must be ignored. Theme words and "
    "Allowed answers are not path evidence. If any required edge is absent, answer "
    "UNKNOWN. Return exactly one displayed Allowed answers label: the reachable DS label "
    "or UNKNOWN. Do not emit a path, identifier explanation, punctuation, or commentary."
)

STRUCTURED_VERIFIER_SYSTEM_PROMPT = (
    "Use only the supplied Link records and the exact RQ start identifier in the Task. "
    "Return one minified JSON object with keys in this exact order: start, destination, "
    "path. For a supported query, path must list every identifier from the requested RQ "
    "through supplied edges to one displayed DS destination. If no complete path exists, "
    "destination must be UNKNOWN and path must contain only the requested start. Ignore "
    "paths rooted at other RQ identifiers. Emit JSON only, with no markdown or commentary."
)

THEMES = (
    "amber cedar river",
    "birch ocean cloud",
    "coral maple stone",
    "daisy lunar grass",
    "frost peach field",
    "olive sandy brook",
    "pearl wheat marsh",
    "slate ivory grove",
)


def arm_system_prompt(arm: str) -> str:
    if arm == "current_v1":
        return CURRENT_V1_SYSTEM_PROMPT
    if arm == "query_anchored_v1":
        return QUERY_ANCHORED_SYSTEM_PROMPT
    if arm == "structured_verifier_v1":
        return STRUCTURED_VERIFIER_SYSTEM_PROMPT
    raise ValueError(f"unknown E3d arm: {arm}")


def arm_prompt_hash(arm: str) -> str:
    template = (
        PROTOCOL
        + "\n"
        + arm
        + "\n"
        + arm_system_prompt(arm)
        + "\nExternal-memory records:\n{records}\n\nTask: {query}\n"
        "Allowed answers: {options}"
    )
    return hashlib.sha256(template.encode("utf-8")).hexdigest()


def build_grounding_messages(
    memories: tuple[MemoryItem, ...], query: Query, arm: str
) -> list[dict[str, str]]:
    if any(memory.bank_id != query.bank_id for memory in memories):
        raise ValueError("E3d prompt cannot mix memory banks")
    records = "\n".join(
        f"M{memory.position}: {memory.text}"
        for memory in sorted(memories, key=lambda item: item.position)
    ) or "(none)"
    return [
        {"role": "system", "content": arm_system_prompt(arm)},
        {
            "role": "user",
            "content": (
                f"External-memory records:\n{records}\n\n"
                f"Task: {query.text}\nAllowed answers: {', '.join(query.options)}"
            ),
        },
    ]


def _requested_start(query: Query) -> str:
    match = re.fullmatch(r"Which destination is reachable from (RQ\d+)\?", query.text)
    if match is None:
        raise ValueError("unknown E3d query form")
    return match.group(1)


def parse_certificate(raw: str) -> dict[str, object] | None:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(value, dict) or list(value) != ["start", "destination", "path"]:
        return None
    if not isinstance(value["start"], str) or not isinstance(value["destination"], str):
        return None
    if not isinstance(value["path"], list) or not value["path"]:
        return None
    if any(not isinstance(node, str) for node in value["path"]):
        return None
    return value


def validate_certificate(
    raw: str, messages: list[dict[str, str]], query: Query
) -> dict[str, object] | None:
    certificate = parse_certificate(raw)
    if certificate is None or certificate["start"] != _requested_start(query):
        return None
    if certificate["path"][0] != certificate["start"]:
        return None
    records = messages[1]["content"].partition("\n\nTask: ")[0]
    edges = set(re.findall(r"Link ([A-Z]+\d+) leads to ([A-Z]+\d+)\.", records))
    graph: dict[str, set[str]] = {}
    for source, target in edges:
        graph.setdefault(source, set()).add(target)
    frontier = [str(certificate["start"])]
    visited: set[str] = set()
    destinations: set[str] = set()
    while frontier:
        node = frontier.pop()
        if node in visited:
            continue
        visited.add(node)
        if node.startswith("DS"):
            destinations.add(node)
        else:
            frontier.extend(graph.get(node, ()))
    destination = certificate["destination"]
    if destination == "UNKNOWN":
        return certificate if certificate["path"] == [certificate["start"]] and not destinations else None
    if destination not in query.options or destination not in destinations:
        return None
    path = certificate["path"]
    if path[-1] != destination or any(
        (source, target) not in edges for source, target in zip(path, path[1:])
    ):
        return None
    return certificate


def parse_grounding_action(
    raw: str, arm: str, query: Query, messages: list[dict[str, str]]
) -> tuple[str | None, bool, dict[str, object] | None]:
    from hibermem.evaluation.scoring import parse_action

    if arm != "structured_verifier_v1":
        action = parse_action(raw, query.options)
        return action, action is not None and raw.strip() == action, None
    certificate = validate_certificate(raw, messages, query)
    if certificate is None:
        return None, False, None
    canonical = json.dumps(certificate, separators=(",", ":"))
    return str(certificate["destination"]), raw == canonical, certificate


def _path_edges(
    requests: list[str], routes: list[str], middles: list[str], targets: list[str],
    chain: int, family: str,
) -> list[tuple[str, str]]:
    if family == "and2":
        return [(requests[chain], routes[chain]), (routes[chain], targets[chain])]
    if family == "and3":
        return [
            (requests[chain], routes[chain]),
            (routes[chain], middles[chain]),
            (middles[chain], targets[chain]),
        ]
    raise ValueError(f"unknown E3d family: {family}")


@dataclass(frozen=True)
class GroundingSuite:
    dataset: ControlledDataset
    stage: str
    arms: tuple[str, ...]
    base_bank_seeds: tuple[int, ...]
    query_metadata: dict[str, dict[str, object]]
    minimal_supports: dict[str, tuple[int, ...]]

    def manifest(self) -> dict[str, object]:
        panels = {
            query.query_id: [panel["evidence_kind"] for panel in self._panels(query)]
            for query in self.dataset.queries
        }
        return {
            **self.dataset.public_manifest(),
            "protocol": PROTOCOL,
            "stage": self.stage,
            "scope": "measurement_instrument_qualification_only",
            "arms": list(self.arms),
            "arm_prompt_sha256": {arm: arm_prompt_hash(arm) for arm in self.arms},
            "base_bank_seeds": list(self.base_bank_seeds),
            "independent_base_banks": len(self.base_bank_seeds),
            "query_metadata": self.query_metadata,
            "minimal_supports_diagnostic_only": {
                key: list(value) for key, value in self.minimal_supports.items()
            },
            "evidence_panels": panels,
            "planned_conditions": sum(len(self._panels(q)) for q in self.dataset.queries)
            * len(self.arms),
            "conditions_per_base_bank_per_arm": 288,
            "future_queries_evaluated": 0,
            "historical_test_access": False,
            "structured_verifier_e4_eligible": False,
        }

    def _panels(self, query: Query) -> list[dict[str, object]]:
        metadata = self.query_metadata[query.query_id]
        support = tuple(int(value) for value in self.minimal_supports[query.query_id])
        other = tuple(int(value) for value in metadata["other_path_positions"])
        full = tuple(range(8))
        panels: list[dict[str, object]] = [
            {"evidence_kind": "empty", "positions": ()},
            {"evidence_kind": "exact_support", "positions": support},
            {"evidence_kind": "full", "positions": full},
        ]
        for link_position, physical in enumerate(support):
            panels.append(
                {
                    "evidence_kind": "missing_exact_link",
                    "positions": tuple(value for value in support if value != physical),
                    "missing_link_position": link_position,
                }
            )
        for link_position, physical in enumerate(support):
            panels.append(
                {
                    "evidence_kind": "missing_full_link",
                    "positions": tuple(value for value in full if value != physical),
                    "missing_link_position": link_position,
                }
            )
        panels.append(
            {
                "evidence_kind": (
                    "other_query_only"
                    if metadata["ledger_mode"] == "dual_path"
                    else "nuisance_only"
                ),
                "positions": other,
            }
        )
        return panels

    def conditions(self):
        view = self.dataset.view(QuerySplit.DISCOVERY)
        for arm in self.arms:
            for query in self.dataset.queries:
                bank = self.dataset.bank(query.bank_id)
                metadata = self.query_metadata[query.query_id]
                support = set(self.minimal_supports[query.query_id])
                for panel_index, panel in enumerate(self._panels(query)):
                    positions = set(int(value) for value in panel["positions"])
                    mask = tuple(index in positions for index in range(8))
                    memories = tuple(
                        memory for memory in bank.memories if memory.position in positions
                    )
                    normalized_kind = (
                        "other_path_only"
                        if panel["evidence_kind"] in ("other_query_only", "nuisance_only")
                        else panel["evidence_kind"]
                    )
                    pairing_key = ":".join(
                        str(value)
                        for value in (
                            arm,
                            metadata["base_bank_seed"],
                            metadata["family"],
                            metadata["overlap"],
                            metadata["world"],
                            metadata["query_role"],
                            normalized_kind,
                            panel.get("missing_link_position", "na"),
                        )
                    )
                    yield {
                        "case_id": f"{arm}:{query.query_id}:p{panel_index:02d}",
                        "arm": arm,
                        "bank": bank,
                        "query": query,
                        "view": view,
                        "mask": mask,
                        "messages": build_grounding_messages(memories, query, arm),
                        "supported": support.issubset(positions),
                        "evidence_kind": panel["evidence_kind"],
                        "missing_link_position": panel.get("missing_link_position"),
                        "pairing_key": pairing_key,
                        **metadata,
                    }


def generate_grounding_suite(
    *, stage: str, base_bank_seeds: list[int], seed: int, families: list[str],
    overlap_levels: list[str], worlds: list[str], ledger_modes: list[str],
    arms: list[str],
) -> GroundingSuite:
    if stage not in ("development", "verification"):
        raise ValueError("E3d stage must be development or verification")
    allowed_arms = DEVELOPMENT_ARMS if stage == "development" else VERIFICATION_ARMS
    if tuple(arms) != allowed_arms:
        raise ValueError(f"E3d {stage} requires the exact frozen arm order")
    for name, values, allowed in (
        ("families", families, FAMILIES),
        ("overlap_levels", overlap_levels, OVERLAPS),
        ("worlds", worlds, WORLDS),
        ("ledger_modes", ledger_modes, LEDGER_MODES),
    ):
        if tuple(values) != allowed:
            raise ValueError(f"E3d requires the exact {name} matrix")
    if type(seed) is not int or not base_bank_seeds or any(type(v) is not int for v in base_bank_seeds):
        raise ValueError("E3d requires integer generator and base-bank seeds")
    if len(set(base_bank_seeds)) != len(base_bank_seeds):
        raise ValueError("E3d base-bank seeds must be unique")

    banks: list[MemoryBank] = []
    queries: list[Query] = []
    answers: dict[str, str] = {}
    metadata: dict[str, dict[str, object]] = {}
    supports: dict[str, tuple[int, ...]] = {}
    for base_seed in base_bank_seeds:
        digest = hashlib.sha256(f"{PROTOCOL}:{seed}:{base_seed}".encode()).digest()
        rng = random.Random(int.from_bytes(digest, "big"))
        identifiers = rng.sample(range(100000, 1000000), 64)
        requests = [f"RQ{x}" for x in identifiers[:8]]
        routes = [f"RT{x}" for x in identifiers[8:16]]
        middles = [f"RK{x}" for x in identifiers[16:24]]
        destinations = [f"DS{x}" for x in identifiers[24:32]]
        distractor_sources = [f"RQ{x}" for x in identifiers[32:40]]
        distractor_targets = [f"DS{x}" for x in identifiers[40:48]]
        options = destinations + ["UNKNOWN"]
        rng.shuffle(options)
        shift = rng.randrange(1, len(destinations))
        counterfactual = destinations[shift:] + destinations[:shift]
        for family, overlap, world, query_role, ledger_mode in product(
            families, overlap_levels, worlds, range(2), ledger_modes
        ):
            path_length = 2 if family == "and2" else 3
            role_rng = random.Random(
                int.from_bytes(
                    hashlib.sha256(
                        f"{PROTOCOL}:{seed}:{base_seed}:{family}:{query_role}".encode()
                    ).digest(),
                    "big",
                )
            )
            logical_order = list(range(8))
            role_rng.shuffle(logical_order)
            physical_by_logical = {
                logical: physical for physical, logical in enumerate(logical_order)
            }
            targets = destinations if world == "base" else counterfactual
            target_chain = query_role
            other_chain = 1 - query_role
            target_edges = _path_edges(
                requests, routes, middles, targets, target_chain, family
            )
            other_edges = _path_edges(
                requests, routes, middles, targets, other_chain, family
            )
            neutral_edges = list(zip(distractor_sources, distractor_targets, strict=True))
            logical_edges: list[tuple[str, str]] = []
            logical_edges.extend(target_edges)
            logical_edges.extend(
                other_edges if ledger_mode == "dual_path" else neutral_edges[:path_length]
            )
            logical_edges.extend(neutral_edges[path_length : path_length + 8 - len(logical_edges)])
            if len(logical_edges) != 8:
                raise AssertionError("E3d ledgers must contain exactly eight records")
            base_id = f"dev-{base_seed}"
            bank_id = (
                f"{base_id}-{family}-{overlap}-{world}-q{query_role}-{ledger_mode}"
            )
            memories = tuple(
                MemoryItem(
                    memory_id=f"{bank_id}-m{physical}",
                    bank_id=bank_id,
                    position=physical,
                    text=(
                        f"Link {logical_edges[logical][0]} leads to "
                        f"{logical_edges[logical][1]}. Theme: "
                        f"{THEMES[0] if overlap == 'high' else THEMES[logical]}."
                    ),
                )
                for physical, logical in enumerate(logical_order)
            )
            bank = MemoryBank(bank_id=bank_id, memories=memories)
            banks.append(bank)
            query_id = f"{bank_id}-target"
            query = Query(
                query_id=query_id,
                bank_id=bank_id,
                split=QuerySplit.DISCOVERY,
                template_family="e3d-grounding-v1",
                dependency_group=f"{base_id}-{family}-q{query_role}",
                text=f"Which destination is reachable from {requests[target_chain]}?",
                options=tuple(options),
            )
            queries.append(query)
            answers[query_id] = targets[target_chain]
            target_positions = tuple(
                physical_by_logical[index] for index in range(path_length)
            )
            other_positions = tuple(
                physical_by_logical[index]
                for index in range(path_length, 2 * path_length)
            )
            supports[query_id] = target_positions
            metadata[query_id] = {
                "base_bank_seed": base_seed,
                "family": family,
                "overlap": overlap,
                "world": world,
                "query_role": query_role,
                "ledger_mode": ledger_mode,
                "target_start": requests[target_chain],
                "target_destination": targets[target_chain],
                "stale_base_destination": destinations[target_chain],
                "other_query_destination": targets[other_chain],
                "target_path_positions": list(target_positions),
                "other_path_positions": list(other_positions),
            }
    dataset = ControlledDataset(
        banks=tuple(banks), queries=tuple(queries), answers=answers, version=PROTOCOL
    )
    return GroundingSuite(
        dataset=dataset,
        stage=stage,
        arms=tuple(arms),
        base_bank_seeds=tuple(base_bank_seeds),
        query_metadata=metadata,
        minimal_supports=supports,
    )


class GroundingOracle(LLMBackend):
    """Prompt-only graph oracle supporting all three frozen E3d interfaces."""

    model_id = "hibermem/mock-e3d-graph-v1"
    model_revision = "1"
    quantization = "none"

    def generate(self, messages, **kwargs):
        del kwargs
        if [message["role"] for message in messages] != ["system", "user"]:
            raise ValueError("E3d oracle requires stateless system/user messages")
        prompt = messages[1]["content"]
        task = prompt.partition("\n\nTask: ")[2]
        start_match = re.search(r"Which destination is reachable from (RQ\d+)\?", task)
        if start_match is None:
            raise ValueError("unknown E3d oracle query")
        start = start_match.group(1)
        edges = re.findall(r"Link ([A-Z]+\d+) leads to ([A-Z]+\d+)\.", prompt)
        graph: dict[str, list[str]] = {}
        for source, target in edges:
            graph.setdefault(source, []).append(target)
        frontier: list[tuple[str, list[str]]] = [(start, [start])]
        seen: set[str] = set()
        found: list[list[str]] = []
        while frontier:
            node, path = frontier.pop(0)
            if node in seen:
                continue
            seen.add(node)
            if node.startswith("DS"):
                found.append(path)
                continue
            frontier.extend((target, [*path, target]) for target in graph.get(node, ()))
        path = found[0] if len(found) == 1 else [start]
        destination = path[-1] if len(found) == 1 else "UNKNOWN"
        if messages[0]["content"] == STRUCTURED_VERIFIER_SYSTEM_PROMPT:
            text = json.dumps(
                {"start": start, "destination": destination, "path": path},
                separators=(",", ":"),
            )
        else:
            text = destination
        return GenerationResult(
            text=text,
            input_tokens=sum(len(message["content"].split()) for message in messages),
            output_tokens=max(1, len(text.split())),
        )


def symbolic_grounding_controls(suite: GroundingSuite) -> dict[str, object]:
    oracle = GroundingOracle()
    counts = {arm: 0 for arm in suite.arms}
    payload_pairs: dict[tuple, dict[str, tuple[int, int]]] = {}
    for case in suite.conditions():
        generated = oracle.generate(case["messages"])
        parsed, strict, certificate = parse_grounding_action(
            generated.text, case["arm"], case["query"], case["messages"]
        )
        reward = case["view"].score(case["query"], parsed)
        if reward != float(case["supported"]):
            raise ValueError(f"E3d symbolic control failed: {case['case_id']}")
        if not case["supported"] and parsed != "UNKNOWN":
            raise ValueError("E3d oracle asserted without complete target support")
        if not strict or (case["arm"] == "structured_verifier_v1") != (certificate is not None):
            raise ValueError("E3d prompt/parser round-trip failed")
        counts[case["arm"]] += 1
        evidence_key = (
            "other_path_only"
            if case["evidence_kind"] in ("other_query_only", "nuisance_only")
            else case["evidence_kind"]
        )
        query_key = (
            case["base_bank_seed"], case["family"], case["overlap"], case["world"],
            case["query_role"], case["arm"], evidence_key,
            case["missing_link_position"],
        )
        payload = (
            len(case["messages"][1]["content"].encode("utf-8")),
            len(case["messages"][1]["content"].split()),
        )
        payload_pairs.setdefault(query_key, {})[case["ledger_mode"]] = payload
    for pair in payload_pairs.values():
        if set(pair) == set(LEDGER_MODES) and pair["single_path"] != pair["dual_path"]:
            raise ValueError("single/dual E3d prompts are not payload matched")
    expected = 288 * len(suite.base_bank_seeds)
    if any(value != expected for value in counts.values()):
        raise ValueError("E3d condition count disagrees with the frozen design")
    return {
        "passed": True,
        "conditions_by_arm": counts,
        "conditions_per_base_bank_per_arm": 288,
        "single_dual_payload_matched": True,
        "prompt_parser_round_trip": True,
        "future_queries_evaluated": 0,
        "historical_test_access": False,
        "scope": "symbolic engineering controls; no model qualification",
    }


__all__ = [
    "DEVELOPMENT_ARMS",
    "LEDGER_MODES",
    "PROTOCOL",
    "VERIFICATION_ARMS",
    "GroundingOracle",
    "GroundingSuite",
    "arm_prompt_hash",
    "build_grounding_messages",
    "generate_grounding_suite",
    "parse_certificate",
    "parse_grounding_action",
    "symbolic_grounding_controls",
    "validate_certificate",
]
