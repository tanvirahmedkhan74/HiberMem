import copy
import hashlib

import pytest

from hibermem.backends import HFLocalBackend
from hibermem.experiments.exact_mechanism import _validate_trace


def valid_trace():
    prompt = "system\nuser"
    return {"rendered_prompt": prompt, "rendered_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "input_token_ids": [1, 2], "generated_token_ids": [3, 4],
            "decoded_with_special_tokens": " DS123456 <eos>",
            "decoded_without_special_tokens": " DS123456 ",
            "text_transform": "decode_skip_special_tokens_then_strip"}


@pytest.mark.parametrize("mutation", ["hash", "tokens", "text", "missing"])
def test_trace_corruption_rejected(mutation):
    trace = valid_trace()
    _validate_trace(trace, "DS123456", 2, 2, False)
    if mutation == "hash":
        trace["rendered_prompt"] += "extra"
    elif mutation == "tokens":
        trace["generated_token_ids"] = [3]
    elif mutation == "text":
        trace["decoded_without_special_tokens"] = "DS000000"
    else:
        trace.pop("decoded_with_special_tokens")
    with pytest.raises(ValueError):
        _validate_trace(trace, "DS123456", 2, 2, False)


def test_hf_generate_captures_trace_without_loading_a_model():
    torch = pytest.importorskip("torch")

    class Tokenizer:
        eos_token_id = 0
        chat_template = "test-only template"

        def apply_chat_template(self, messages, **kwargs):
            return "\n".join(message["content"] for message in messages)

        def __call__(self, text, **kwargs):
            return {"input_ids": torch.tensor([[1, 2]])}

        def decode(self, tokens, skip_special_tokens):
            return " DS123456 " if skip_special_tokens else " DS123456 <eos>"

    class Model:
        def generate(self, **kwargs):
            assert kwargs["do_sample"] is False
            return torch.tensor([[1, 2, 3, 4]])

        def parameters(self):
            return [torch.tensor([1.0])]

    # Deliberately bypass the constructor and supply CPU tensor/model stubs.
    backend = object.__new__(HFLocalBackend)
    backend._torch, backend._tokenizer, backend._model = torch, Tokenizer(), Model()
    backend.model_id, backend.model_revision, backend.quantization = "stub", "a" * 40, "none"
    backend.device, backend.dtype, backend.trust_remote_code = "cpu", "float32", False
    result = backend.generate([{"role": "system", "content": "system"}, {"role": "user", "content": "user"}])
    assert result.text == "DS123456" and result.trace == valid_trace()
    _validate_trace(result.trace, result.text, result.input_tokens, result.output_tokens, False)
    assert backend.provenance()["resolved_parameter_dtypes"] == "torch.float32"
    assert backend.provenance()["resolved_parameter_devices"] == "cpu"
