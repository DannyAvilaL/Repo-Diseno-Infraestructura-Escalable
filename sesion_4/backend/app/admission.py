"""Control de admisión con cola acotada (bounded queue) y backpressure.

Fundamento teórico: un servidor de inferencia tiene capacidad finita (slots de batch/KV cache).
Si se acepta tráfico sin límite, la latencia crece sin cota (cola infinita). Se aplica
*load shedding*: cola máxima + timeout, y se responde 429/503 en lugar de degradar a todos.
La profundidad de cola es, además, la mejor señal de escalamiento horizontal.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from .metrics import Metrics


class QueueFullError(Exception):
    """La cola de espera alcanzó su máximo: se rechaza de inmediato (HTTP 429)."""


class QueueTimeoutError(Exception):
    """Esperó demasiado en cola: se rechaza (HTTP 503)."""


class AdmissionController:
    def __init__(self, max_concurrency: int, max_queue: int, queue_timeout_s: float, metrics: Metrics) -> None:
        self._sem = asyncio.Semaphore(max_concurrency)
        self._max_queue = max_queue
        self._timeout = queue_timeout_s
        self._waiting = 0
        self._m = metrics

    @property
    def waiting(self) -> int:
        return self._waiting

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[float]:
        """Adquiere un slot de inferencia. Entrega el tiempo esperado en cola (segundos)."""
        loop = asyncio.get_running_loop()
        started = loop.time()

        # Camino rápido: hay slot libre, no se entra a la cola.
        if not self._sem.locked():
            await self._sem.acquire()
        else:
            if self._waiting >= self._max_queue:
                self._m.rejected.labels(reason="queue_full").inc()
                raise QueueFullError("cola llena")
            self._waiting += 1
            self._m.queue_depth.set(self._waiting)
            try:
                await asyncio.wait_for(self._sem.acquire(), timeout=self._timeout)
            except asyncio.TimeoutError as exc:
                self._m.rejected.labels(reason="queue_timeout").inc()
                raise QueueTimeoutError("timeout en cola") from exc
            finally:
                self._waiting -= 1
                self._m.queue_depth.set(self._waiting)

        waited = loop.time() - started
        self._m.queue_wait.observe(waited)
        self._m.in_flight.inc()
        try:
            yield waited
        finally:
            self._m.in_flight.dec()
            self._sem.release()
