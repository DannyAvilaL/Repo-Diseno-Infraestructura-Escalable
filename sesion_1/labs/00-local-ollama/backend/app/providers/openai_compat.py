"""Adaptador para endpoints compatibles con la API Chat Completions de OpenAI.

Sirve para la Demo 2 ("misma API, dos backends"): el mismo backend puede
apuntar al endpoint /v1 de Ollama o a un modelo gestionado que exponga una
API compatible. Verifique en la documentación del proveedor la URL base y el
esquema de autenticación vigentes antes de usarlo.
"""

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


class OpenAICompatProvider(InferenceProvider):
    name = "openai_compat"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None,
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
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout, headers=headers
        )

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[StreamEvent]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            "temperature": self._temperature,
            "max_tokens": self._max_output_tokens,
        }
        request = self._client.build_request("POST", "/chat/completions", json=payload)
        response = await open_stream_with_retries(self._client, request, self._max_retries)
        try:
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError as exc:
                    raise ProviderError(f"Evento SSE inválido: {data_str[:120]}") from exc
                for choice in data.get("choices") or []:
                    text = (choice.get("delta") or {}).get("content")
                    if text:
                        yield TextChunk(text)
                usage = data.get("usage")
                if usage:
                    yield Usage(
                        prompt_tokens=usage.get("prompt_tokens"),
                        completion_tokens=usage.get("completion_tokens"),
                    )
        except httpx.ReadTimeout as exc:
            raise ProviderError("Tiempo de espera agotado durante la generación") from exc
        finally:
            await response.aclose()

    async def health(self) -> None:
        try:
            response = await self._client.get("/models")
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"El endpoint compatible no responde: {exc}") from exc
        # Validado contra Ollama 0.40.3: /v1/models responde 200 aunque el modelo
        # configurado no exista, por eso se comprueba el identificador.
        # Ollama 0.40.3 responde {"data": null} cuando no hay modelos.
        try:
            data = response.json().get("data") or []
        except (ValueError, AttributeError) as exc:
            raise ProviderError("Respuesta inválida de /models") from exc
        ids = {m.get("id") for m in data if isinstance(m, dict)}
        if ids and self.model not in ids:
            raise ProviderError(f"El modelo '{self.model}' no está disponible en el endpoint")
        if not ids:
            raise ProviderError(f"El endpoint no lista modelos; '{self.model}' no está disponible")

    async def aclose(self) -> None:
        await self._client.aclose()
