"""Fábrica de proveedores a partir de la configuración."""

from __future__ import annotations

import httpx

from ..config import Settings
from .base import InferenceProvider, ProviderError, TextChunk, Usage
from .ollama import OllamaProvider
from .openai_compat import OpenAICompatProvider

__all__ = ["InferenceProvider", "ProviderError", "TextChunk", "Usage", "build_provider"]


def build_provider(settings: Settings) -> InferenceProvider:
    timeout = httpx.Timeout(settings.read_timeout_s, connect=settings.connect_timeout_s)
    common = {
        "temperature": settings.temperature,
        "max_output_tokens": settings.max_output_tokens,
        "timeout": timeout,
        "max_retries": settings.max_retries,
    }
    if settings.provider == "ollama":
        return OllamaProvider(str(settings.ollama_base_url), settings.model, **common)
    if settings.openai_base_url is None:
        raise ValueError("APP_OPENAI_BASE_URL es obligatorio con APP_PROVIDER=openai_compat")
    return OpenAICompatProvider(
        str(settings.openai_base_url), settings.model, settings.openai_api_key, **common
    )
