from hibermem.coalition.cache import CacheKey, EvaluationCache


def _key(query_id: str = "q1") -> CacheKey:
    return CacheKey(
        model_id="model",
        model_revision="revision",
        prompt_template_hash="prompt",
        memory_bank_id="bank",
        query_id=query_id,
        coalition_mask="v1:2:1",
        generation_config={"do_sample": False, "max_new_tokens": 8},
        seed=1,
        code_commit="abc",
    )


def test_cache_key_uniqueness() -> None:
    assert _key("q1").digest() != _key("q2").digest()


def test_cache_resume(tmp_path) -> None:
    path = tmp_path / "evaluations.sqlite3"
    with EvaluationCache(path) as cache:
        cache.put(
            _key(),
            raw_output="A",
            parsed_action="A",
            reward=1.0,
            latency_seconds=0.1,
            input_tokens=10,
            output_tokens=1,
        )
        assert cache.count() == 1

    with EvaluationCache(path) as resumed:
        value = resumed.get(_key())
        assert value is not None
        assert value.reward == 1.0
        assert resumed.count() == 1
