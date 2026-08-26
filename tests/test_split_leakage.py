import pytest

from hibermem.environments.controlled import QuerySplit, generate_phase2_dataset
from hibermem.experiments.phase2 import SplitLeakageError, require_discovery_view


def test_discovery_test_isolation() -> None:
    dataset = generate_phase2_dataset(1)
    require_discovery_view(dataset.view(QuerySplit.DISCOVERY))
    with pytest.raises(SplitLeakageError):
        require_discovery_view(dataset.view(QuerySplit.TEST))


def test_split_capability_cannot_score_another_splits_query() -> None:
    dataset = generate_phase2_dataset(1)
    discovery = dataset.view(QuerySplit.DISCOVERY)
    test_query = dataset.view(QuerySplit.TEST).queries[0]
    with pytest.raises(PermissionError):
        discovery.score(test_query, test_query.options[0])
