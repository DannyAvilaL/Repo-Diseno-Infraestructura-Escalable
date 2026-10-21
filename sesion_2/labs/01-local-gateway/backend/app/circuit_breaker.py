"""Circuit breaker por región.

Estados (patrón descrito por Nygard en *Release It!* y usado por los API
gateways gestionados):

- ``closed``: la región recibe tráfico. Se cuentan las fallas en una ventana
  deslizante; al alcanzar el umbral, el circuito se abre.
- ``open``: la región NO recibe tráfico durante ``open_s`` segundos. Si el
  proveedor respondió 429 con ``Retry-After``, se usa ese tiempo (con el tope
  ``max_open_s``), como recomienda la guía de gateways de Azure OpenAI.
- ``half_open``: vencido el tiempo, se deja pasar UNA solicitud de prueba. Si
  tiene éxito, el circuito se cierra; si falla, vuelve a abrirse.

El reloj es inyectable para probar las transiciones sin esperar.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from typing import Literal

State = Literal["closed", "open", "half_open"]


class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int,
        failure_window_s: float,
        open_s: float,
        max_open_s: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._threshold = failure_threshold
        self._window = failure_window_s
        self._open_s = open_s
        self._max_open_s = max_open_s
        self._clock = clock
        self._failures: deque[float] = deque()
        self._state: State = "closed"
        self._opened_until = 0.0
        self._probe_in_flight = False

    @property
    def state(self) -> State:
        if self._state == "open" and self._clock() >= self._opened_until:
            self._state = "half_open"
            self._probe_in_flight = False
        return self._state

    def open_remaining_s(self) -> float:
        if self.state != "open":
            return 0.0
        return max(0.0, self._opened_until - self._clock())

    def allow_request(self) -> bool:
        """Indica si se puede enviar una solicitud y reserva la prueba en half-open."""
        state = self.state
        if state == "closed":
            return True
        if state == "half_open" and not self._probe_in_flight:
            self._probe_in_flight = True
            return True
        return False

    def would_allow(self) -> bool:
        """Como ``allow_request`` pero sin reservar la prueba (para ordenar candidatos)."""
        state = self.state
        return state == "closed" or (state == "half_open" and not self._probe_in_flight)

    def record_success(self) -> None:
        self._failures.clear()
        self._state = "closed"
        self._probe_in_flight = False

    def record_failure(self, retry_after_s: float | None = None) -> None:
        now = self._clock()
        if self.state == "half_open":
            self._trip(now, retry_after_s)
            return
        if retry_after_s is not None and retry_after_s > 0:
            # 429 con Retry-After: el proveedor indica cuándo volver.
            self._trip(now, retry_after_s)
            return
        self._failures.append(now)
        while self._failures and now - self._failures[0] > self._window:
            self._failures.popleft()
        if len(self._failures) >= self._threshold:
            self._trip(now, None)

    def release_probe(self) -> None:
        """Libera la reserva de prueba si la solicitud no llegó a enviarse."""
        self._probe_in_flight = False

    def force_open(self, seconds: float) -> None:
        self._trip(self._clock(), seconds)

    def _trip(self, now: float, retry_after_s: float | None) -> None:
        duration = self._open_s if retry_after_s is None else retry_after_s
        self._state = "open"
        self._opened_until = now + min(duration, self._max_open_s)
        self._failures.clear()
        self._probe_in_flight = False
