from hibermem.backends import MockBackend
from hibermem.environments.controlled import (
    QuerySplit,
    build_messages,
    generate_phase2_dataset,
)
from hibermem.evaluation import parse_action


def test_phase2_dataset_has_locked_scale_and_disjoint_templates() -> None:
    dataset = generate_phase2_dataset()
    assert len(dataset.banks) == 10
    assert all(len(bank.memories) == 8 for bank in dataset.banks)
    assert all(memory.storage_tokens == 7 for bank in dataset.banks for memory in bank.memories)
    assert all(memory.storage_bytes == 48 for bank in dataset.banks for memory in bank.memories)
    assert len(dataset.view(QuerySplit.DISCOVERY).queries) == 200
    assert len(dataset.view(QuerySplit.VALIDATION).queries) == 100
    assert len(dataset.view(QuerySplit.TEST).queries) == 200

    families = {
        split: {query.template_family for query in dataset.view(split).queries}
        for split in QuerySplit
    }
    assert families[QuerySplit.DISCOVERY].isdisjoint(families[QuerySplit.VALIDATION])
    assert families[QuerySplit.DISCOVERY].isdisjoint(families[QuerySplit.TEST])
    assert families[QuerySplit.VALIDATION].isdisjoint(families[QuerySplit.TEST])
    assert "answer" not in str(dataset.public_manifest()).lower()

    for bank in dataset.banks:
        bank_queries = dataset.view(QuerySplit.DISCOVERY).for_bank(bank.bank_id)
        for chain in range(4):
            request = bank.memories[chain * 2].text.split()[1]
            route = bank.memories[chain * 2].text.split()[-1].rstrip(".")
            destination = bank.memories[chain * 2 + 1].text.split()[-1].rstrip(".")
            assert request[-1] != route[-1]
            assert destination[-1] not in {request[-1], route[-1]}
            assert bank_queries[chain * 5].options.index(route) != chain


def test_mock_backend_requires_the_expected_memory_dependency() -> None:
    dataset = generate_phase2_dataset(1)
    bank = dataset.banks[0]
    view = dataset.view(QuerySplit.DISCOVERY)
    direct = view.for_bank(bank.bank_id)[0]
    final = view.for_bank(bank.bank_id)[1]
    backend = MockBackend()

    direct_output = backend.generate(build_messages((bank.memories[0],), direct)).text
    final_incomplete = backend.generate(build_messages((bank.memories[0],), final)).text
    final_complete = backend.generate(
        build_messages((bank.memories[0], bank.memories[1]), final)
    ).text

    assert view.score(direct, parse_action(direct_output, direct.options)) == 1.0
    assert view.score(final, parse_action(final_incomplete, final.options)) == 0.0
    assert view.score(final, parse_action(final_complete, final.options)) == 1.0


def test_bank_start_creates_fresh_deterministic_banks() -> None:
    original = generate_phase2_dataset(2)
    calibration = generate_phase2_dataset(2, bank_start=100)

    assert [bank.bank_id for bank in calibration.banks] == ["bank-100", "bank-101"]
    assert calibration.sha256() == generate_phase2_dataset(2, bank_start=100).sha256()
    assert calibration.sha256() != original.sha256()
