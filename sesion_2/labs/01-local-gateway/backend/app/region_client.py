"""Cliente asíncrono de una región compatible con la API Chat Completions.

Funciona con el simulador del laboratorio, con el endpoint /v1 de Ollama y con
servicios gestionados que expongan una API compatible (por ejemplo, el
endpoint ``/openai/v1`` de Microsoft Foundry). Clasifica cada falla para que
el router decida si conmuta a otra región:

- Reintentables (conmutar): error de conexión, tiempo de espera del primer
  byte, 429 y 5xx.
- No reintentables (devolver al cliente): 4xx distintos de 429, porque la
  solicitud fallaría igual en cualquier región.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from .config import RegionConfig


class RegionError(RuntimeError):
    def __init__(
        self,
        region: str,
        message: str,
        *,
        retryable: bool,
        status_code: int | None = None,
        retry_after_s: float | None = None,
    ) -> None:
        super().__init__(message)
        self.region = region
        self.retryable = retryable
        self.status_code = status_code
        self.retry_after_s = retry_after_s


@dataclass(frozen=True)
class TextChunk:
    text: str


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int | None
    completion_tokens: int | None


StreamEvent = TextChunk | Usage


def parse_retry_after(headers: httpx.Headers) -> float | None:
    """Lee ``retry-after-ms`` (Azure OpenAI) o ``Retry-After`` en segundos."""
    ms = headers.get("retry-after-ms")
    if ms:
        try:
            return max(0.0, float(ms) / 1000)
        except ValueError:
            pass
    value = headers.get("retry-after")
    if value:
        try:
            return max(0.0, float(value))
        except ValueError:
            return None  # formato fecha HTTP: se usa el tiempo de apertura por defecto
    return None


class RegionClient:
    def __init__(
        self,
        cfg: RegionConfig,
        *,
        connect_timeout_s: float,
        first_byte_timeout_s: float,
        read_timeout_s: float,
        health_timeout_s: float,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.cfg = cfg
        self.name = cfg.name
        self.model = cfg.model
        self._first_byte_timeout_s = first_byte_timeout_s
        self._health_timeout_s = health_timeout_s
        headers: dict[str, str] = {}
        key = cfg.api_key()
        if key:
            if cfg.auth_header == "api-key":
                headers["api-key"] = key
            else:
                headers["Authorization"] = f"Bearer {key}"
        self._client = client or httpx.AsyncClient(
            base_url=str(cfg.base_url).rstrip("/"),
            timeout=httpx.Timeout(read_timeout_s, connect=connect_timeout_s),
            headers=headers,
        )

    def _payload(self, messages: list[dict[str, str]], *, max_tokens: int, temperature: float, stream: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream_options"] = {"include_usage": True}
        return payload

    async def _send(self, request: httpx.Request, *, stream: bool) -> httpx.Response:
        try:
            response = await asyncio.wait_for(
                self._client.send(request, stream=stream), timeout=self._first_byte_timeout_s
            )
        except TimeoutError as exc:
            raise RegionError(self.name, "Tiempo de espera del primer byte agotado", retryable=True) from exc
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
            raise RegionError(self.name, f"Sin conexión con la región: {type(exc).__name__}", retryable=True) from exc
        except httpx.TimeoutException as exc:
            raise RegionError(self.name, "Tiempo de espera agotado", retryable=True) from exc
        if response.status_code >= 400:
            body = (await response.aread()).decode(errors="replace")[:200]
            await response.aclose()
            retryable = response.status_code == 429 or response.status_code >= 500
            raise RegionError(
                self.name,
                f"HTTP {response.status_code}: {body}",
                retryable=retryable,
                status_code=response.status_code,
                retry_after_s=parse_retry_after(response.headers) if response.status_code == 429 else None,
            )
        return response

    async def open_stream(self, messages: list[dict[str, str]], *, max_tokens: int, temperature: float) -> httpx.Response:
        request = self._client.build_request(
            "POST", "/chat/completions",
            json=self._payload(messages, max_tokens=max_tokens, temperature=temperature, stream=True),
        )
        return await self._send(request, stream=True)

    async def iter_stream(self, response: httpx.Response) -> AsyncIterator[StreamEvent]:
        """Recorre los eventos SSE. Una falla aquí ya NO admite conmutación."""
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
                    raise RegionError(self.name, "Evento SSE inválido", retryable=False) from exc
                for choice in data.get("choices") or []:
                    text = (choice.get("delta") or {}).get("content")
                    if text:
                        yield TextChunk(text)
                usage = data.get("usage")
                if usage:
                    yield Usage(usage.get("prompt_tokens"), usage.get("completion_tokens"))
        except httpx.HTTPError as exc:
            raise RegionError(self.name, f"Corte durante la generación: {type(exc).__name__}", retryable=False) from exc
        finally:
            await response.aclose()

    async def complete(self, messages: list[dict[str, str]], *, max_tokens: int, temperature: float) -> dict[str, Any]:
        """Solicitud sin streaming (la usa el procesador de lotes)."""
        request = self._client.build_request(
            "POST", "/chat/completions",
            json=self._payload(messages, max_tokens=max_tokens, temperature=temperature, stream=False),
        )
        response = await self._send(request, stream=False)
        try:
            body = response.json()
        except ValueError as exc:
            raise RegionError(self.name, "Respuesta no JSON", retryable=True) from exc
        if not isinstance(body, dict) or not body.get("choices"):
            raise RegionError(self.name, "Respuesta sin 'choices'", retryable=True)
        return body

    async def health(self) -> None:
        try:
            response = await self._client.get(self.cfg.health_path, timeout=self._health_timeout_s)
        except httpx.HTTPError as exc:
            raise RegionError(self.name, f"Health check sin respuesta: {type(exc).__name__}", retryable=True) from exc
        if response.status_code >= 400:
            raise RegionError(self.name, f"Health check HTTP {response.status_code}", retryable=True, status_code=response.status_code)
        if not self.cfg.check_model:
            return
        try:
            data = response.json().get("data") or []  # Ollama puede responder {"data": null}
        except (ValueError, AttributeError) as exc:
            raise RegionError(self.name, "Health check con respuesta inválida", retryable=True) from exc
        ids = {m.get("id") for m in data if isinstance(m, dict)}
        if self.model not in ids:
            raise RegionError(self.name, f"El modelo '{self.model}' no está disponible", retryable=False)

    async def aclose(self) -> None:
        await self._client.aclose()
