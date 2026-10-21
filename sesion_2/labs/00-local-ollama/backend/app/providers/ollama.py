"""Adaptador para la API nativa de Ollama (/api/chat, respuesta NDJSON)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from .base import (
    InferenceProvider,
    ProviderError,
    StreamEvent,
    TextChunk,
    Usage,
    open_stream_with_retries,
)


class OllamaProvider(InferenceProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        temperature: float,
        max_output_tokens: int,
        timeout: httpx.Timeout,
        max_retries: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._max_retries = max_retries
        self._client = client or httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[StreamEvent]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": self._temperature, "num_predict": self._max_output_tokens},
        }
        request = self._client.build_request("POST", "/api/chat", json=payload)
        response = await open_stream_with_retries(self._client, request, self._max_retries)
        try:
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ProviderError(f"Respuesta NDJSON inválida: {line[:120]}") from exc
                if "error" in data:
                    raise ProviderError(f"Ollama: {data['error']}")
                text = (data.get("message") or {}).get("content", "")
                if text:
                    yield TextChunk(text)
                if data.get("done"):
                    yield Usage(
                        prompt_tokens=data.get("prompt_eval_count"),
                        completion_tokens=data.get("eval_count"),
                    )
        except httpx.ReadTimeout as exc:
            raise ProviderError("Tiempo de espera agotado durante la generación") from exc
        finally:
            await response.aclose()

    async def health(self) -> None:
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama no responde: {exc}") from exc
        names = {m.get("name") for m in response.json().get("models", [])}
        if self.model not in names and f"{self.model}:latest" not in names:
            raise ProviderError(
                f"El modelo '{self.model}' no está descargado. Ejecute: ollama pull {self.model}"
            )

    async def aclose(self) -> None:
        await self._client.aclose()
