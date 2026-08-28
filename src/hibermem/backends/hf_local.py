"""Lazy local Hugging Face causal-language-model backend."""

from __future__ import annotations

from typing import Any

from .base import GenerationResult, LLMBackend, Message


class HFLocalBackend(LLMBackend):
    """Run deterministic greedy inference without importing Transformers globally."""

    def __init__(
        self,
        *,
        model_id: str,
        model_revision: str,
        device: str = "cuda",
        dtype: str = "float16",
        quantization: str = "none",
        local_files_only: bool = False,
        trust_remote_code: bool = False,
    ) -> None:
        if quantization != "none":
            raise ValueError("the initial local backend supports quantization='none' only")
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:
            raise RuntimeError(
                "HF local inference requires the optional 'llm' dependencies"
            ) from error

        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but PyTorch cannot see a CUDA device")
        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        if dtype not in dtype_map:
            raise ValueError("dtype must be float16, bfloat16, or float32")

        self.model_id = model_id
        self.model_revision = model_revision
        self.quantization = quantization
        self.device = device
        self.dtype = dtype
        self.trust_remote_code = trust_remote_code
        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            revision=model_revision,
            local_files_only=local_files_only,
            trust_remote_code=trust_remote_code,
        )
        model_kwargs = {
            "revision": model_revision,
            "dtype": dtype_map[dtype],
            "low_cpu_mem_usage": True,
            "local_files_only": local_files_only,
            "trust_remote_code": trust_remote_code,
        }
        try:
            self._model = AutoModelForCausalLM.from_pretrained(
                model_id, **model_kwargs
            ).to(device)
        except TypeError as error:
            # Compatibility path for older supported Transformers releases.
            if "dtype" not in str(error):
                raise
            model_kwargs["torch_dtype"] = model_kwargs.pop("dtype")
            self._model = AutoModelForCausalLM.from_pretrained(
                model_id, **model_kwargs
            ).to(device)
        self._model.eval()

    def generate(self, messages: list[Message], **kwargs: object) -> GenerationResult:
        do_sample = bool(kwargs.get("do_sample", False))
        if do_sample:
            raise ValueError("Phase 2 core generation must be deterministic")
        max_new_tokens = int(kwargs.get("max_new_tokens", 8))
        seed = int(kwargs.get("seed", 0))
        self._torch.manual_seed(seed)
        if self.device == "cuda":
            self._torch.cuda.manual_seed_all(seed)

        rendered = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs: dict[str, Any] = self._tokenizer(rendered, return_tensors="pt")
        inputs = {name: tensor.to(self.device) for name, tensor in inputs.items()}
        input_length = int(inputs["input_ids"].shape[-1])
        with self._torch.inference_mode():
            generated = self._model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=max_new_tokens,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        new_tokens = generated[0, input_length:]
        text = self._tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        return GenerationResult(
            text=text,
            input_tokens=input_length,
            output_tokens=int(new_tokens.shape[-1]),
        )

    def provenance(self) -> dict[str, str]:
        provenance = super().provenance()
        provenance.update(
            {
                "device": self.device,
                "dtype": self.dtype,
                "trust_remote_code": str(self.trust_remote_code).lower(),
            }
        )
        return provenance
