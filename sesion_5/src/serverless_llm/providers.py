"""Proveedores de inferencia.

* ``MockProvider``: determinista, simula carga de modelo (cold start), TTFT y TPOT.
  Permite estudiar patrones serverless sin GPU ni cuenta cloud.
* ``OllamaProvider``: inferencia real local vía la API REST de Ollama.

Ambos exponen la misma interfaz (``LLMProvider``), de modo que añadir Bedrock,
Foundry o Gemini es implementar tres métodos (ver ``labs/``).
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from .config import Settings


@dataclass(slots=True)
class GenerationRequest:
    prompt: str
    system: str | None = None
    temperature: float = 0.0
    max_tokens: int = 256


@dataclass(slots=True)
class GenerationResult:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    ttft_ms: float | None = None
    load_ms: float | None = None  # tiempo de carga del modelo (cold start del modelo)
    extra: dict[str, float] = field(default_factory=dict)


class ProviderError(RuntimeError):
    """Error del proveedor (red, timeout, respuesta inválida). Es reintentable."""


class LLMProvider(Protocol):
    name: str
    model: str

    async def startup(self) -> float:
        """Inicializa el proveedor. Devuelve la duración de la inicialización en segundos."""

    async def generate(self, req: GenerationRequest) -> GenerationResult: ...

    def stream(self, req: GenerationRequest) -> AsyncIterator[str]: ...

    async def ready(self) -> bool: ...

    async def aclose(self) -> None: ...


def _approx_tokens(text: str) -> int:
    """Aproximación didáctica (≈ palabras). No usar para facturación real."""
    return max(1, len(text.split()))


class MockProvider:
    """Simula un LLM con latencias configurables.

    La primera inferencia (si ``startup`` no se ejecutó) paga ``cold_start_s``
    como si estuviera cargando pesos en memoria. Las latencias son SIMULADAS:
    sirven para razonar sobre arquitectura, no como benchmark de un modelo real.
    """

    name = "mock"
    model = "mock-llm-1"

    def __init__(self, settings: Settings) -> None:
        self._cold_start_s = settings.mock_cold_start_s
        self._ttft_s = settings.mock_ttft_ms / 1000
        self._tpot_s = settings.mock_tpot_ms / 1000
        self._loaded = False
        self._load_lock = asyncio.Lock()

    async def startup(self) -> float:
        started = time.perf_counter()
        await self._ensure_loaded()
        return time.perf_counter() - started

    async def _ensure_loaded(self) -> float:
        """Carga perezosa con lock: solo UNA petición paga la carga."""
        if self._loaded:
            return 0.0
        async with self._load_lock:
            if self._loaded:
                return 0.0
            started = time.perf_counter()
            await asyncio.sleep(self._cold_start_s)
            self._loaded = True
            return time.perf_counter() - started

    @staticmethod
    def _compose(req: GenerationRequest) -> str:
        head = "Respuesta simulada"
        if req.system:
            head += " (con instrucción de sistema)"
        words = req.prompt.split()
        echo = " ".join(words[: min(len(words), req.max_tokens)])
        return f"{head}: {echo}"

    async def generate(self, req: GenerationRequest) -> GenerationResult:
        load_s = await self._ensure_loaded()
        text = self._compose(req)
        completion_tokens = min(_approx_tokens(text), req.max_tokens)
        await asyncio.sleep(self._ttft_s + completion_tokens * self._tpot_s)
        return GenerationResult(
            text=text,
            model=self.model,
            prompt_tokens=_approx_tokens(req.prompt),
            completion_tokens=completion_tokens,
            ttft_ms=self._ttft_s * 1000,
            load_ms=load_s * 1000 if load_s else None,
        )

    async def stream(self, req: GenerationRequest) -> AsyncIterator[str]:
        await self._ensure_loaded()
        await asyncio.sleep(self._ttft_s)
        for token in self._compose(req).split():
            yield token + " "
            await asyncio.sleep(self._tpot_s)

    async def ready(self) -> bool:
        return self._loaded

    async def aclose(self) -> None:
        return None


class OllamaProvider:
    """Cliente asíncrono de la API nativa de Ollama (``/api/chat``)."""

    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.model = settings.ollama_model
        self._keep_alive = settings.ollama_keep_alive
        self._client = httpx.AsyncClient(
            base_url=settings.ollama_base_url,
            timeout=httpx.Timeout(settings.request_timeout_s, connect=5.0),
        )

    def _payload(self, req: GenerationRequest, stream: bool) -> dict[str, object]:
        messages: list[dict[str, str]] = []
        if req.system:
            messages.append({"role": "system", "content": req.system})
        messages.append({"role": "user", "content": req.prompt})
        return {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "keep_alive": self._keep_alive,
            "options": {"temperature": req.temperature, "num_predict": req.max_tokens},
        }

    async def startup(self) -> float:
        """Precarga el modelo en memoria (petición sin mensajes = load only)."""
        started = time.perf_counter()
        try:
            resp = await self._client.post(
                "/api/generate", json={"model": self.model, "keep_alive": self._keep_alive}
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - requiere Ollama real
            raise ProviderError(f"No se pudo precargar el modelo en Ollama: {exc}") from exc
        return time.perf_counter() - started

    async def generate(self, req: GenerationRequest) -> GenerationResult:
        try:
            resp = await self._client.post("/api/chat", json=self._payload(req, stream=False))
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"Error al invocar Ollama: {exc}") from exc
        ns = 1_000_000  # nanosegundos -> milisegundos
        prompt_eval_ms = data.get("prompt_eval_duration", 0) / ns
        return GenerationResult(
            text=data.get("message", {}).get("content", ""),
            model=data.get("model", self.model),
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            completion_tokens=int(data.get("eval_count", 0)),
            # Aproximación: TTFT ≈ carga + prefill (la API no entrega TTFT exacto sin streaming)
            ttft_ms=data.get("load_duration", 0) / ns + prompt_eval_ms,
            load_ms=data.get("load_duration", 0) / ns or None,
            extra={"prompt_eval_ms": prompt_eval_ms, "eval_ms": data.get("eval_duration", 0) / ns},
        )

    async def stream(self, req: GenerationRequest) -> AsyncIterator[str]:
        try:
            async with self._client.stream(
                "POST", "/api/chat", json=self._payload(req, stream=True)
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    piece = chunk.get("message", {}).get("content", "")
                    if piece:
                        yield piece
                    if chunk.get("done"):
                        break
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"Error en streaming de Ollama: {exc}") from exc

    async def ready(self) -> bool:
        try:
            resp = await self._client.get("/api/tags", timeout=2.0)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def aclose(self) -> None:
        await self._client.aclose()


def build_provider(settings: Settings) -> LLMProvider:
    if settings.provider == "ollama":
        return OllamaProvider(settings)
    return MockProvider(settings)
