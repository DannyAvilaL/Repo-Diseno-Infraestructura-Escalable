"""Router multi-región: selección de candidatos, failover y health checks.

Decisiones de diseño (ver ADR-0007 y la Unidad C de la Sesión 2):

1. **Orden de candidatos.** Con ``priority`` (activo-pasivo) se usan primero
   las regiones de menor número de prioridad; con ``round_robin``
   (activo-activo) todas las regiones sanas se alternan según su peso.
2. **Señales de salud.** Se combinan una señal *activa* (health check
   periódico a ``/models``, que no consume capacidad del modelo) y una señal
   *pasiva* (circuit breaker alimentado por los errores reales).
3. **Conmutación solo antes del primer token.** Si una región falla después de
   haber enviado texto al usuario, reintentar en otra duplicaría la respuesta;
   en ese caso se informa el error.
4. **Presupuesto de intentos.** ``max_attempts`` limita cuántas regiones se
   prueban por solicitud, para no amplificar la carga durante un incidente.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import httpx

from .circuit_breaker import CircuitBreaker
from .config import Settings
from .region_client import RegionClient, RegionError
from .schemas import RegionStatus, RegionsResponse

logger = logging.getLogger("gateway.router")


class NoRegionAvailable(RuntimeError):
    """Ninguna región pudo atender la solicitud."""

    def __init__(self, message: str, errors: list[str]) -> None:
        super().__init__(message)
        self.errors = errors


@dataclass
class RegionState:
    client: RegionClient
    breaker: CircuitBreaker
    healthy: bool = True
    health_detail: str | None = None
    disabled: bool = False
    inflight: int = 0
    requests: int = 0
    successes: int = 0
    failures: int = 0
    last_error: str | None = None
    ewma_ttft_ms: float | None = None
    _alpha: float = field(default=0.3, repr=False)

    @property
    def name(self) -> str:
        return self.client.name

    def observe_ttft(self, ttft_ms: float | None) -> None:
        if ttft_ms is None:
            return
        self.ewma_ttft_ms = ttft_ms if self.ewma_ttft_ms is None else (
            self._alpha * ttft_ms + (1 - self._alpha) * self.ewma_ttft_ms
        )


class Router:
    def __init__(
        self,
        settings: Settings,
        *,
        clients: Sequence[RegionClient] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        clients = clients or [
            RegionClient(
                cfg,
                connect_timeout_s=settings.connect_timeout_s,
                first_byte_timeout_s=settings.first_byte_timeout_s,
                read_timeout_s=settings.read_timeout_s,
                health_timeout_s=settings.health_timeout_s,
            )
            for cfg in settings.regions
        ]
        self.regions: dict[str, RegionState] = {
            c.name: RegionState(
                client=c,
                breaker=CircuitBreaker(
                    failure_threshold=settings.cb_failure_threshold,
                    failure_window_s=settings.cb_failure_window_s,
                    open_s=settings.cb_open_s,
                    max_open_s=settings.cb_max_open_s,
                    clock=clock,
                ),
            )
            for c in clients
        }
        self.online_inflight = 0
        self._rotation = 0
        self._health_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ orden
    def _rotate(self, group: list[RegionState]) -> list[RegionState]:
        expanded = [r for r in group for _ in range(r.client.cfg.weight)]
        if not expanded:
            return []
        start = self._rotation % len(expanded)
        ordered: list[RegionState] = []
        for r in expanded[start:] + expanded[:start]:
            if r not in ordered:
                ordered.append(r)
        return ordered

    def candidates(self) -> list[RegionState]:
        """Regiones elegibles en orden de preferencia (sin efectos secundarios)."""
        enabled = [r for r in self.regions.values() if not r.disabled and r.breaker.would_allow()]
        if self.settings.routing == "round_robin":
            groups = [enabled]
        else:
            prios = sorted({r.client.cfg.priority for r in enabled})
            groups = [[r for r in enabled if r.client.cfg.priority == p] for p in prios]
        ordered = [r for g in groups for r in self._rotate(g)]
        # Las regiones que fallan el health check quedan al final: se usan solo
        # si no hay alternativa (la señal activa puede estar desactualizada).
        return [r for r in ordered if r.healthy] + [r for r in ordered if not r.healthy]

    def available_regions(self) -> list[str]:
        return [r.name for r in self.candidates() if r.healthy]

    # ------------------------------------------------------- resultado intento
    def _start(self, state: RegionState) -> None:
        state.inflight += 1
        state.requests += 1

    def release(self, state: RegionState) -> None:
        """Libera el intento sin culpar a la región (p. ej., el cliente se desconectó)."""
        state.inflight = max(0, state.inflight - 1)
        state.breaker.release_probe()

    def finish(self, state: RegionState, *, ok: bool, ttft_ms: float | None = None, error: RegionError | None = None) -> None:
        """Cierra un intento: estadísticas y circuit breaker."""
        state.inflight = max(0, state.inflight - 1)
        if ok:
            state.successes += 1
            state.breaker.record_success()
            state.observe_ttft(ttft_ms)
            return
        state.failures += 1
        state.last_error = str(error) if error else "error"
        if error is None or error.retryable:
            state.breaker.record_failure(error.retry_after_s if error else None)
        else:
            state.breaker.release_probe()

    # -------------------------------------------------------------- ejecución
    async def _try_regions(self, call: Callable[[RegionState], Any]) -> tuple[RegionState, Any, int]:
        candidates = self.candidates()
        self._rotation += 1
        if not candidates:
            raise NoRegionAvailable("No hay regiones disponibles (circuitos abiertos o deshabilitadas)", [])
        errors: list[str] = []
        attempts = 0
        for state in candidates:
            if attempts >= self.settings.max_attempts:
                break
            if not state.breaker.allow_request():
                continue
            attempts += 1
            self._start(state)
            try:
                result = await call(state)
            except RegionError as exc:
                errors.append(f"{state.name}: {exc}")
                if not exc.retryable:
                    self.finish(state, ok=False, error=exc)
                    raise
                self.finish(state, ok=False, error=exc)
                logger.warning(
                    "conmutacion_region",
                    extra={"region": state.name, "attempt": attempts, "status": exc.status_code, "error": str(exc)[:120]},
                )
                continue
            return state, result, attempts
        raise NoRegionAvailable("Todas las regiones intentadas fallaron", errors)

    async def open_stream(self, messages: list[dict[str, str]], *, max_tokens: int, temperature: float) -> tuple[RegionState, httpx.Response, int]:
        """Abre el stream en la primera región que responda.

        El llamador DEBE invocar ``finish`` al terminar de consumir el stream.
        """
        async def call(state: RegionState) -> httpx.Response:
            return await state.client.open_stream(messages, max_tokens=max_tokens, temperature=temperature)

        return await self._try_regions(call)

    async def complete(self, messages: list[dict[str, str]], *, max_tokens: int, temperature: float) -> tuple[RegionState, dict[str, Any], int]:
        async def call(state: RegionState) -> dict[str, Any]:
            return await state.client.complete(messages, max_tokens=max_tokens, temperature=temperature)

        state, body, attempts = await self._try_regions(call)
        self.finish(state, ok=True)
        return state, body, attempts

    # ----------------------------------------------------------- health check
    async def check_health_once(self) -> None:
        async def check(state: RegionState) -> None:
            try:
                await state.client.health()
            except RegionError as exc:
                if state.healthy:
                    logger.warning("region_no_saludable", extra={"region": state.name, "detail": str(exc)})
                state.healthy, state.health_detail = False, str(exc)
            else:
                if not state.healthy:
                    logger.info("region_recuperada", extra={"region": state.name})
                state.healthy, state.health_detail = True, None

        await asyncio.gather(*(check(s) for s in self.regions.values()))

    async def _health_loop(self) -> None:
        while True:
            try:
                await self.check_health_once()
            except Exception:  # pragma: no cover - el bucle nunca debe morir
                logger.exception("error_health_check")
            await asyncio.sleep(self.settings.health_interval_s)

    def start(self) -> None:
        if self._health_task is None:
            self._health_task = asyncio.create_task(self._health_loop())

    async def stop(self) -> None:
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            self._health_task = None
        await asyncio.gather(*(s.client.aclose() for s in self.regions.values()))

    # ----------------------------------------------------------------- estado
    def status(self) -> RegionsResponse:
        regions = []
        for s in self.regions.values():
            cfg = s.client.cfg
            regions.append(
                RegionStatus(
                    name=s.name,
                    priority=cfg.priority,
                    weight=cfg.weight,
                    model=cfg.model,
                    healthy=s.healthy,
                    health_detail=s.health_detail,
                    circuit=s.breaker.state,
                    circuit_open_remaining_s=round(s.breaker.open_remaining_s(), 1),
                    disabled=s.disabled,
                    inflight=s.inflight,
                    requests=s.requests,
                    successes=s.successes,
                    failures=s.failures,
                    last_error=s.last_error,
                    ewma_ttft_ms=round(s.ewma_ttft_ms, 1) if s.ewma_ttft_ms is not None else None,
                    sim_admin_url=str(cfg.sim_admin_url) if cfg.sim_admin_url else None,
                )
            )
        return RegionsResponse(routing=self.settings.routing, online_inflight=self.online_inflight, regions=regions)
