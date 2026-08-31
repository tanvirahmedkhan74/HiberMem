"""E3a lexical-nuisance x functional-dependency games; development only.

The prompt-reading oracle and the diagnostic support antichains are independent
implementations. Neither answers nor support metadata are passed to real models.
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass
from itertools import combinations, product
from statistics import fmean

from hibermem.backends.base import GenerationResult, LLMBackend
from hibermem.coalition.masks import iter_masks, mask_to_index
from hibermem.memory import MemoryItem
from .dataset import ControlledDataset, MemoryBank, Query, QuerySplit

PROTOCOL = "phase2r-factorial-mechanism-v1"
FAMILIES = ("direct", "and2", "or2", "and3")
OVERLAPS = ("low", "high")
WORLDS = ("base", "counterfactual")
VARIANTS = ("original", "reverse_records", "reverse_options")
SYSTEM_PROMPT = (
    "Resolve the requested destination using only supplied Link records. A Link X leads to Y "
    "record is a directed edge. Start at the requested RQ identifier and follow a complete "
    "path of one or more supplied edges to a DS destination. Match identifiers exactly. "
    "Duplicate edges are interchangeable: either copy is sufficient. Theme words are "
    "non-operative metadata and never establish links. Unrelated records and Allowed answers "
    "are not evidence for a path. If no complete path exists, answer UNKNOWN. Do not infer "
    "missing edges or guess from option order. Return exactly one label from Allowed answers, "
    "with no explanation."
)
THEMES = (
    "amber cedar river", "birch ocean cloud", "coral maple stone", "daisy lunar grass",
    "frost peach field", "olive sandy brook", "pearl wheat marsh", "slate ivory grove",
)


def prompt_template_hash():
    return hashlib.sha256((PROTOCOL + "\n" + SYSTEM_PROMPT +
                           "\nExternal-memory records:\n{records}\n\nTask: {query}\n"
                           "Allowed answers: {options}").encode()).hexdigest()


def supported_by(mask, minimal_sets):
    """Disjunction of sufficient sets, not conjunction of their union (OR matters)."""
    return any(all(mask[i] for i in support) for support in minimal_sets)


def lexical_overlap(bank):
    tokens = [set(re.findall(r"[a-z0-9]+", memory.text.lower())) for memory in bank.memories]
    return fmean(len(a & b) / len(a | b) for a, b in combinations(tokens, 2))


@dataclass(frozen=True)
class FactorialSuite:
    dataset: ControlledDataset
    minimal_supports: dict[str, tuple[tuple[int, ...], ...]]
    game_metadata: dict[str, dict]
    query_metadata: dict[str, dict]

    def manifest(self):
        return {
            **self.dataset.public_manifest(), "protocol": PROTOCOL,
            "scope": "development_only", "n_memories": 8,
            "minimal_supports_diagnostic_only": {
                key: [list(s) for s in value] for key, value in self.minimal_supports.items()},
            "games": self.game_metadata, "query_metadata": self.query_metadata,
            "planned_conditions": len(self.dataset.queries) * 256,
            "independent_base_banks": len({g["base_bank_id"] for g in self.game_metadata.values()}),
            "overlap_interpretation": "lexical theme overlap, not validated semantic similarity",
            "query_shift": "none; paired development manipulations, not future queries",
            "history": "fresh system and user messages for every condition",
        }

    def conditions(self):
        view = self.dataset.view(QuerySplit.DISCOVERY)
        for query in self.dataset.queries:
            bank = self.dataset.bank(query.bank_id)
            variant = self.game_metadata[bank.bank_id]["variant"]
            for mask in iter_masks(8):
                records = [f"M{i}: {m.text}" for i, m in enumerate(bank.memories) if mask[i]]
                if variant == "reverse_records":
                    records.reverse()
                memory_text = "\n".join(records) or "(none)"
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"External-memory records:\n{memory_text}\n\n"
                     f"Task: {query.text}\nAllowed answers: {', '.join(query.options)}"},
                ]
                yield {"case_id": f"{query.query_id}:{mask_to_index(mask):03d}",
                       "bank": bank, "query": query, "view": view, "mask": mask,
                       "messages": messages, "supported": supported_by(mask, self.minimal_supports[query.query_id])}


class FactorialOracle(LLMBackend):
    """Reads only the supplied prompt, not the suite, expected target or support sets."""

    model_id = "hibermem/mock-factorial-graph-v1"
    model_revision = "1"
    quantization = "none"

    def generate(self, messages, **kwargs):
        del kwargs
        if [message["role"] for message in messages] != ["system", "user"]:
            raise ValueError("the factorial oracle requires stateless messages")
        prompt = messages[1]["content"]
        records, separator, task = prompt.partition("\n\nTask: ")
        question = re.search(r"Which destination is reachable from (RQ\d+)\?", task)
        if not separator or not question:
            raise ValueError("unknown factorial prompt")
        graph = {}
        for source, target in re.findall(r"Link ([A-Z]+\d+) leads to ([A-Z]+\d+)\.", records):
            graph.setdefault(source, set()).add(target)
        frontier, visited, destinations = [question.group(1)], set(), set()
        while frontier:
            node = frontier.pop()
            if node in visited:
                continue
            visited.add(node)
            if node.startswith("DS"):
                destinations.add(node)
            else:
                frontier.extend(graph.get(node, ()))
        answer = next(iter(destinations)) if len(destinations) == 1 else "UNKNOWN"
        return GenerationResult(text=answer, input_tokens=sum(len(m["content"].split()) for m in messages),
                                output_tokens=1)


def generate_factorial_suite(*, n_banks, bank_start, seed, families, overlap_levels, worlds, variants):
    if any(type(value) is not int for value in (n_banks, bank_start, seed)):
        raise ValueError("integer development settings required")
    if n_banks < 1 or bank_start < 340 or bank_start + n_banks > 360:
        raise ValueError("factorial development banks must stay inside [340,360)")
    for name, values, allowed in (("families", families, FAMILIES), ("overlap_levels", overlap_levels, OVERLAPS),
                                  ("worlds", worlds, WORLDS), ("variants", variants, VARIANTS)):
        if (not isinstance(values, list) or not values or any(v not in allowed for v in values)
                or len(set(values)) != len(values)):
            raise ValueError(f"invalid {name}")
    if worlds != list(WORLDS) or overlap_levels != list(OVERLAPS) or variants[0] != "original":
        raise ValueError("paired worlds/overlap and an original presentation are required")
    banks, queries, answers, supports, games, query_meta = [], [], {}, {}, {}, {}
    for bank_index in range(bank_start, bank_start + n_banks):
        # Independent of requested count/order of variants and families; reproducible submatrices.
        bank_seed = int.from_bytes(hashlib.sha256(f"{PROTOCOL}:{seed}:{bank_index}".encode()).digest(), "big")
        rng = random.Random(bank_seed)
        ids = rng.sample(range(100000, 1000000), 40)
        requests = [f"RQ{x}" for x in ids[:8]]
        routes = [f"RT{x}" for x in ids[8:16]]
        middles = [f"RK{x}" for x in ids[16:24]]
        destinations = [f"DS{x}" for x in ids[24:32]]
        order = list(range(8))
        rng.shuffle(order)
        positions = {logical: position for position, logical in enumerate(order)}
        options = destinations + ["UNKNOWN"]
        rng.shuffle(options)
        shift = rng.randrange(1, len(destinations))  # Derangement, never changes answer options.
        counterfactual = destinations[shift:] + destinations[:shift]
        for family, overlap, world, variant in product(families, overlap_levels, worlds, variants):
            base_id = f"dev-{bank_index}"
            bank_id = f"{base_id}-{family}-{overlap}-{world}-{variant}"
            targets = destinations if world == "base" else counterfactual
            edges, logical_supports = [], []
            for chain in range(2):
                offset = 3 * chain
                nulls = [(requests[chain + 2], targets[chain + 2]), (routes[chain + 4], targets[chain + 4])]
                if family == "direct":
                    block = [(requests[chain], targets[chain]), *nulls]
                    minimal = ((offset,),)
                elif family == "and2":
                    block = [(requests[chain], routes[chain]), (routes[chain], targets[chain]), nulls[1]]
                    minimal = ((offset, offset + 1),)
                elif family == "or2":
                    block = [(requests[chain], targets[chain]), (requests[chain], targets[chain]), nulls[1]]
                    minimal = ((offset,), (offset + 1,))
                else:
                    block = [(requests[chain], routes[chain]), (routes[chain], middles[chain]),
                             (middles[chain], targets[chain])]
                    minimal = ((offset, offset + 1, offset + 2),)
                edges.extend(block)
                logical_supports.append(minimal)
            edges.extend([(requests[6], targets[6]), (requests[7], targets[7])])
            memories = tuple(MemoryItem(
                memory_id=f"{bank_id}-m{position}", bank_id=bank_id, position=position,
                text=f"Link {edges[logical][0]} leads to {edges[logical][1]}. "
                     f"Theme: {THEMES[0] if overlap == 'high' else THEMES[logical]}.",
            ) for position, logical in enumerate(order))
            bank = MemoryBank(bank_id, memories)
            banks.append(bank)
            metadata = {"base_bank_id": base_id, "family": family, "overlap": overlap,
                        "world": world, "variant": variant}
            games[bank_id] = {**metadata, "mean_record_token_jaccard": lexical_overlap(bank)}
            for chain in range(2):
                query_id = f"{bank_id}-q{chain}"
                query = Query(query_id=query_id, bank_id=bank_id, split=QuerySplit.DISCOVERY,
                              template_family="e3-graph-v1", dependency_group=f"{base_id}-chain-{chain}",
                              text=f"Which destination is reachable from {requests[chain]}?",
                              options=tuple(options[::-1] if variant == "reverse_options" else options))
                queries.append(query)
                answers[query_id] = targets[chain]
                supports[query_id] = tuple(sorted(tuple(sorted(positions[i] for i in s))
                                                 for s in logical_supports[chain]))
                query_meta[query_id] = {**metadata, "chain": chain,
                                      "motif_players_in_role_order": [positions[3 * chain + i] for i in range(3)]}
    dataset = ControlledDataset(banks=tuple(banks), queries=tuple(queries), answers=answers, version=PROTOCOL)
    return FactorialSuite(dataset, supports, games, query_meta)


def symbolic_controls(suite):
    oracle = FactorialOracle()
    from hibermem.evaluation.scoring import parse_action

    checked = copied_correct = option_correct = unsupported_copied = unsupported_option = 0
    for case in suite.conditions():
        query, view = case["query"], case["view"]
        answer = oracle.generate(case["messages"]).text
        reward = view.score(query, parse_action(answer, query.options))
        if reward != float(case["supported"]) or (not case["supported"] and answer != "UNKNOWN"):
            raise ValueError(f"text oracle disagrees with structural support: {case['case_id']}")
        records = case["messages"][1]["content"].partition("\n\nTask: ")[0]
        labels = re.findall(r"DS\d+", records)
        copy_score = view.score(query, labels[0] if labels else "UNKNOWN")
        first_score = view.score(query, query.options[0])
        copied_correct += copy_score
        option_correct += first_score
        unsupported_copied += copy_score * (not case["supported"])
        unsupported_option += first_score * (not case["supported"])
        checked += 1
    return {"passed": True, "symbolic_complete_game_checks": checked,
            "scope": "engineering grammar/support controls, not model qualification",
            "shortcut_scores_all_conditions": {
                "destination_copy_accuracy": copied_correct / checked,
                "first_option_accuracy": option_correct / checked,
                "destination_copy_unsupported_correct": unsupported_copied / checked,
                "first_option_unsupported_correct": unsupported_option / checked},
            "shortcut_interpretation": "shortcuts need not have zero interactions in every factorial family"}
