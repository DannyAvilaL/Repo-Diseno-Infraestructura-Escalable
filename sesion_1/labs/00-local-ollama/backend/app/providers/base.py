"""Abstracción del proveedor de inferencia.

El backend no conoce el proveedor concreto: cambiar de Ollama a un servicio
gestionado es cambiar de adaptador y de configuración (Unidad B, D.5).
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """Error del proveedor que el backend traduce a HTTP 502/503."""


@dataclass(frozen=True)
class TextChunk:
    text: str


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int | None
    completion_tokens: int | None


StreamEvent = TextChunk | Usage


class InferenceProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[StreamEvent]:
        """Genera fragmentos de texto y, al final, el uso de tokens si existe."""

    @abstractmethod
    async def health(self) -> None:
        """Lanza ProviderError si el proveedor o el modelo no están disponibles."""

    async def aclose(self) -> None:  # pragma: no cover - por defecto no hay recursos
        return None


async def open_stream_with_retries(
    client: httpx.AsyncClient,
    request: httpx.Request,
    max_retries: int,
) -> httpx.Response:
    """Abre la respuesta en streaming con reintentos SOLO antes del primer byte.

    Reintentar después de haber emitido tokens duplicaría texto al usuario,
    por eso los reintentos se limitan a errores de conexión y a 429/5xx.
    """
    attempt = 0
    while True:
        try:
            response = await client.send(request, stream=True)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            if attempt >= max_retries:
                raise ProviderError(f"No se pudo conectar con el proveedor: {exc}") from exc
        else:
            if response.status_code < 400:
                return response
            body = (await response.aread()).decode(errors="replace")[:300]
            await response.aclose()
            retryable = response.status_code == 429 or response.status_code >= 500
            if not retryable or attempt >= max_retries:
                raise ProviderError(f"El proveedor respondió {response.status_code}: {body}")
        attempt += 1
        backoff = min(0.5 * 2**attempt, 4.0)
        logger.warning("reintento_proveedor", extra={"attempt": attempt, "backoff_s": backoff})
        await asyncio.sleep(backoff)
