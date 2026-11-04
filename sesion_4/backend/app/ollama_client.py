"""Cliente asíncrono para la API /api/chat de Ollama (NDJSON en streaming)."""

import json
from typing import Any, AsyncIterator

import httpx


class UpstreamError(Exception):
    """Fallo del servidor de inferencia (HTTP 502 hacia el cliente)."""


class OllamaClient:
    def __init__(self, base_url: str, timeout_s: float, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_s, connect=5.0),
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def is_ready(self, model: str) -> bool:
        """Listo = el servidor responde y el modelo está descargado (volumen poblado)."""
        try:
            r = await self._client.get("/api/tags", timeout=3.0)
            r.raise_for_status()
        except httpx.HTTPError:
            return False
        names = {m.get("name") for m in r.json().get("models", [])}
        return model in names or f"{model}:latest" in names

    async def stream_chat(
        self, model: str, messages: list[dict[str, str]], max_tokens: int, temperature: float
    ) -> AsyncIterator[dict[str, Any]]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        try:
            async with self._client.stream("POST", "/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", "replace")[:200]
                    raise UpstreamError(f"ollama HTTP {resp.status_code}: {body}")
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise UpstreamError("respuesta NDJSON inválida") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError(f"fallo de red hacia ollama: {exc.__class__.__name__}") from exc
