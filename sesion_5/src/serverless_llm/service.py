"""Servicio de chat: orquesta guardas, caché, backpressure e inferencia."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator

from .cache import ResponseCache, make_cache_key
from .config import Settings
from .metrics import Metrics
from .providers import GenerationRequest, LLMProvider
from .schemas import ChatRequest, ChatResponse, Timings, Usage
from .security import InputGuard, fingerprint, redact_pii, sanitize_output

log = logging.getLogger("sllm.service")


class RejectedError(Exception):
    """La petición fue rechazada por política (validación, límite o saturación)."""

    def __init__(self, reason: str, status_code: int, retry_after_s: float | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code
        self.retry_after_s = retry_after_s


class InstanceState:
    """Modela el ciclo de vida de una *instancia* serverless.

    ``instance_id`` identifica el "execution environment" (Lambda) / "revision
    replica" (Container Apps) / "instance" (Cloud Run). ``cold_start`` es True
    únicamente para la PRIMERA petición atendida por la instancia.
    """

    def __init__(self) -> None:
        self.instance_id = uuid.uuid4().hex[:8]
        self.created_at = time.monotonic()
        self.init_seconds = 0.0
        self._served = 0

    def claim_cold_start(self) -> bool:
        is_cold = self._served == 0
        self._served += 1
        return is_cold

    @property
    def served(self) -> int:
        return self._served


class ChatService:
    def __init__(
        self,
        *,
        settings: Settings,
        provider: LLMProvider,
        metrics: Metrics,
        instance: InstanceState,
    ) -> None:
        self._settings = settings
        self._provider = provider
        self._metrics = metrics
        self._instance = instance
        self._guard = InputGuard(
            max_chars=settings.max_prompt_chars, injection_policy=settings.injection_policy
        )
        self._sem = asyncio.Semaphore(settings.max_concurrency)
        self.cache: ResponseCache[ChatResponse] = ResponseCache(
            ttl_s=settings.cache_ttl_s,
            max_entries=settings.cache_max_entries,
            enabled=settings.cache_enabled,
        )

    # ------------------------------------------------------------------
    def _prepare(self, tenant: str, req: ChatRequest) -> tuple[GenerationRequest, list[str]]:
        verdict = self._guard.check(req.prompt)
        if not verdict.allowed:
            self._metrics.rejected.labels(reason=verdict.reason or "input").inc()
            raise RejectedError(verdict.reason or "input_rejected", 422)
        system_verdict = self._guard.check(req.system) if req.system else None
        if system_verdict and not system_verdict.allowed:
            self._metrics.rejected.labels(reason="system_" + (system_verdict.reason or "x")).inc()
            raise RejectedError("system_" + (system_verdict.reason or "rejected"), 422)
        max_tokens = min(req.max_tokens, self._settings.max_output_tokens)
        # Logging seguro: huella + longitud, nunca el contenido en claro.
        log.info(
            "chat tenant=%s prompt_fp=%s chars=%d flags=%s",
            tenant,
            fingerprint(verdict.sanitized),
            len(verdict.sanitized),
            verdict.flags,
        )
        if self._settings.log_level.upper() == "DEBUG" and self._settings.redact_pii_in_logs:
            log.debug("prompt(redactado)=%s", redact_pii(verdict.sanitized)[:200])
        gen = GenerationRequest(
            prompt=verdict.sanitized,
            system=system_verdict.sanitized if system_verdict else None,
            temperature=req.temperature,
            max_tokens=max_tokens,
        )
        return gen, verdict.flags

    async def _acquire_slot(self) -> float:
        """Backpressure: espera acotada por una ranura de inferencia o falla rápido (429)."""
        started = time.perf_counter()
        try:
            await asyncio.wait_for(self._sem.acquire(), timeout=self._settings.queue_wait_timeout_s)
        except TimeoutError as exc:
            self._metrics.rejected.labels(reason="saturated").inc()
            raise RejectedError(
                "saturated", 429, retry_after_s=self._settings.queue_wait_timeout_s
            ) from exc
        return (time.perf_counter() - started) * 1000

    # ------------------------------------------------------------------
    async def chat(self, tenant: str, req: ChatRequest) -> ChatResponse:
        started = time.perf_counter()
        gen, flags = self._prepare(tenant, req)
        cold = self._instance.claim_cold_start()
        if cold:
            self._metrics.cold_starts.inc()

        key = make_cache_key(
            tenant=tenant,
            model=self._provider.model,
            prompt=gen.prompt,
            system=gen.system,
            temperature=gen.temperature,
            max_tokens=gen.max_tokens,
        )
        wait_ms = 0.0

        async def compute() -> ChatResponse:
            nonlocal wait_ms
            wait_ms = await self._acquire_slot()
            self._metrics.inflight.inc()
            try:
                result = await self._provider.generate(gen)
            finally:
                self._metrics.inflight.dec()
                self._sem.release()
            text, out_flags = sanitize_output(result.text)
            self._metrics.tokens.labels(kind="prompt").inc(result.prompt_tokens)
            self._metrics.tokens.labels(kind="completion").inc(result.completion_tokens)
            if result.ttft_ms is not None:
                self._metrics.ttft.observe(result.ttft_ms / 1000)
            return ChatResponse(
                text=text,
                model=result.model,
                usage=Usage(
                    prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens
                ),
                timings=Timings(
                    total_ms=0.0, queue_wait_ms=wait_ms, ttft_ms=result.ttft_ms, load_ms=result.load_ms
                ),
                instance_id=self._instance.instance_id,
                flags=out_flags,
            )

        outcome = await self.cache.get_or_compute(key, compute, cacheable=gen.temperature == 0.0)
        label = "hit" if outcome.hit else ("coalesced" if outcome.coalesced else "miss")
        self._metrics.cache.labels(result=label).inc()
        base = outcome.value
        return base.model_copy(
            update={
                "cache_hit": outcome.hit,
                "coalesced": outcome.coalesced,
                "cold_start": cold,
                "instance_id": self._instance.instance_id,
                "flags": sorted(set(base.flags) | set(flags)),
                "timings": base.timings.model_copy(
                    update={"total_ms": (time.perf_counter() - started) * 1000}
                ),
            }
        )

    async def stream(self, tenant: str, req: ChatRequest) -> AsyncIterator[str]:
        gen, _flags = self._prepare(tenant, req)
        if self._instance.claim_cold_start():
            self._metrics.cold_starts.inc()
        await self._acquire_slot()
        self._metrics.inflight.inc()
        started = time.perf_counter()
        first = True
        try:
            async for piece in self._provider.stream(gen):
                if first:
                    self._metrics.ttft.observe(time.perf_counter() - started)
                    first = False
                safe, _ = sanitize_output(piece)
                yield safe
        finally:
            self._metrics.inflight.dec()
            self._sem.release()
