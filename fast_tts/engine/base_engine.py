# -*- coding: utf-8 -*-
# Time      :2025/3/29 11:17
# Author    :Hui Huang
import platform
import random
from typing import Literal, Optional, Callable, AsyncIterator
import soundfile as sf
import torch
import numpy as np
from ..llm import initialize_llm
from .utils import split_text
from functools import partial
from abc import ABC, abstractmethod


class BaseEngine(ABC):
    SAMPLE_RATE = 16000

    def __init__(
            self,
            llm_model_path: str,
            max_length: int = 32768,
            llm_device: Literal["cpu", "cuda", "mps", "auto"] | str = "auto",
            backend: Literal["vllm", "llama-cpp", "sglang", "torch"] = "torch",
            llm_attn_implementation: Optional[Literal["sdpa", "flash_attention_2", "eager"]] = None,
            torch_dtype: Literal['float16', "bfloat16", 'float32', 'auto'] = "auto",
            llm_gpu_memory_utilization: Optional[float] = 0.6,
            cache_implementation: Optional[str] = None,
            batch_size: int = 32,
            seed: int = 0,
            stop_tokens: Optional[list[str]] = None,
            stop_token_ids: Optional[list[int]] = None,
            **kwargs
    ):
        self.generator = initialize_llm(
            model_path=llm_model_path,
            backend=backend,
            max_length=max_length,
            device=self._auto_detect_device(llm_device),
            attn_implementation=llm_attn_implementation,
            torch_dtype=torch_dtype,
            gpu_memory_utilization=llm_gpu_memory_utilization,
            cache_implementation=cache_implementation,
            batch_size=batch_size,
            seed=seed,
            stop_tokens=stop_tokens,
            stop_token_ids=stop_token_ids,
            **kwargs
        )

    @classmethod
    def set_seed(cls, seed: int):
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    @classmethod
    def _auto_detect_device(cls, device: str):
        if device in ["cpu", "cuda", "mps"] or device.startswith("cuda"):
            return device
        if torch.cuda.is_available():
            return "cuda"
        elif platform.system() == "Darwin" and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def write_audio(self, audio: np.ndarray, filepath: str):
        sf.write(filepath, audio, self.SAMPLE_RATE, "PCM_16")

    def split_text(
            self,
            text: str,
            length_threshold: int = 50,
            window_size: int = 50,
            split_fn: Optional[Callable[[str], list[str]]] = None
    ) -> list[str]:
        tokenize_fn = partial(
            self.generator.tokenizer.encode,
            add_special_tokens=False,
            truncation=False,
            padding=False
        )
        return split_text(
            text, window_size,
            tokenize_fn=tokenize_fn,
            split_fn=split_fn,
            length_threshold=length_threshold
        )

    @abstractmethod
    async def speak_async(
            self,
            name: str,
            text: str,
            temperature: float = 0.9,
            top_k: int = 50,
            top_p: float = 0.95,
            max_tokens: int = 4096,
            length_threshold: int = 50,
            window_size: int = 50,
            split_fn: Optional[Callable[[str], list[str]]] = None,
            **kwargs) -> np.ndarray:
        ...

    @abstractmethod
    async def speak_stream_async(
            self,
            name: str,
            text: str,
            temperature: float = 0.9,
            top_k: int = 50,
            top_p: float = 0.95,
            max_tokens: int = 4096,
            length_threshold: int = 50,
            window_size: int = 50,
            split_fn: Optional[Callable[[str], list[str]]] = None,
            **kwargs) -> AsyncIterator[np.ndarray]:
        yield  # type: ignore

    @abstractmethod
    async def clone_voice_async(
            self,
            text: str,
            reference_audio,
            reference_text: Optional[str] = None,
            temperature: float = 0.9,
            top_k: int = 50,
            top_p: float = 0.95,
            max_tokens: int = 4096,
            length_threshold: int = 50,
            window_size: int = 50,
            split_fn: Optional[Callable[[str], list[str]]] = None,
            **kwargs) -> np.ndarray:
        ...

    @abstractmethod
    async def clone_voice_stream_async(
            self,
            text: str,
            reference_audio,
            reference_text: Optional[str] = None,
            temperature: float = 0.9,
            top_k: int = 50,
            top_p: float = 0.95,
            max_tokens: int = 4096,
            length_threshold: int = 50,
            window_size: int = 50,
            split_fn: Optional[Callable[[str], list[str]]] = None,
            **kwargs) -> AsyncIterator[np.ndarray]:
        yield  # type: ignore

    @abstractmethod
    async def generate_voice_async(
            self,
            text: str,
            gender: Optional[Literal["female", "male"]] = "female",
            pitch: Optional[Literal["very_low", "low", "moderate", "high", "very_high"]] = "moderate",
            speed: Optional[Literal["very_low", "low", "moderate", "high", "very_high"]] = "moderate",
            temperature: float = 0.9,
            top_k: int = 50,
            top_p: float = 0.95,
            max_tokens: int = 4096,
            length_threshold: int = 50,
            window_size: int = 50,
            split_fn: Optional[Callable[[str], list[str]]] = None,
            **kwargs) -> np.ndarray:
        ...

    @abstractmethod
    async def generate_voice_stream_async(
            self,
            text: str,
            gender: Optional[Literal["female", "male"]] = "female",
            pitch: Optional[Literal["very_low", "low", "moderate", "high", "very_high"]] = "moderate",
            speed: Optional[Literal["very_low", "low", "moderate", "high", "very_high"]] = "moderate",
            temperature: float = 0.9,
            top_k: int = 50,
            top_p: float = 0.95,
            max_tokens: int = 4096,
            length_threshold: int = 50,
            window_size: int = 50,
            split_fn: Optional[Callable[[str], list[str]]] = None,
            **kwargs) -> AsyncIterator[np.ndarray]:
        yield  # type: ignore
