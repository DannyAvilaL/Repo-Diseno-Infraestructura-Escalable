"""Caché de respuestas LLM con TTL, LRU y *single-flight*.

Decisiones de diseño (ver docs/01-marco-teorico.md §6):

* Solo se cachea de forma segura cuando la salida es (casi) determinista:
  ``temperature == 0``. Con temperatura > 0 el mismo prompt puede producir
  respuestas legítimamente distintas.
* La clave incluye al **tenant**: evita fuga entre clientes (OWASP LLM02).
* *Single-flight*: N peticiones idénticas concurrentes comparten UNA inferencia
  (mitiga la "estampida" tras un cold start o una expiración de caché).
* Esta implementación es por-instancia (en memoria). En serverless real cada
  instancia tendría su propia caché; para compartirla se usa Redis/ElastiCache,
  Memorystore o Azure Cache for Redis (ver docs/02-arquitecturas-referencia.md).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


def make_cache_key(
    *, tenant: str, model: str, prompt: str, system: str | None, temperature: float, max_tokens: int
) -> str:
    canonical = json.dumps(
        {
            "tenant": tenant,
            "model": model,
            # Normalización mínima: espacios en los extremos no cambian la semántica
            "prompt": prompt.strip(),
            "system": (system or "").strip(),
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class CacheStats:
    hits: int = 0
    misses: int = 0
    coalesced: int = 0
    evictions: int = 0
    expirations: int = 0

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


@dataclass(slots=True)
class LookupOutcome[T]:
    value: T
    hit: bool
    coalesced: bool


class ResponseCache[T]:
    def __init__(
        self,
        *,
        ttl_s: float,
        max_entries: int,
        clock: Callable[[], float] = time.monotonic,
        enabled: bool = True,
    ) -> None:
        self._ttl_s = ttl_s
        self._max_entries = max_entries
        self._clock = clock
        self._enabled = enabled
        self._store: OrderedDict[str, tuple[float, T]] = OrderedDict()
        self._inflight: dict[str, asyncio.Future[T]] = {}
        self.stats = CacheStats()

    def __len__(self) -> int:
        return len(self._store)

    def _get(self, key: str) -> T | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if self._clock() >= expires_at:
            del self._store[key]
            self.stats.expirations += 1
            return None
        self._store.move_to_end(key)  # LRU
        return value

    def _set(self, key: str, value: T) -> None:
        self._store[key] = (self._clock() + self._ttl_s, value)
        self._store.move_to_end(key)
        while len(self._store) > self._max_entries:
            self._store.popitem(last=False)
            self.stats.evictions += 1

    async def get_or_compute(
        self, key: str, compute: Callable[[], Awaitable[T]], *, cacheable: bool
    ) -> LookupOutcome[T]:
        """Devuelve el valor cacheado o lo calcula una sola vez (single-flight)."""
        if not (self._enabled and cacheable):
            return LookupOutcome(await compute(), hit=False, coalesced=False)

        cached = self._get(key)
        if cached is not None:
            self.stats.hits += 1
            return LookupOutcome(cached, hit=True, coalesced=False)

        pending = self._inflight.get(key)
        if pending is not None:
            self.stats.coalesced += 1
            return LookupOutcome(await asyncio.shield(pending), hit=False, coalesced=True)

        self.stats.misses += 1
        future: asyncio.Future[T] = asyncio.get_running_loop().create_future()
        self._inflight[key] = future
        try:
            value = await compute()
        except BaseException as exc:
            future.set_exception(exc)
            future.exception()  # marca la excepción como "consumida" si nadie más espera
            raise
        else:
            self._set(key, value)
            future.set_result(value)
            return LookupOutcome(value, hit=False, coalesced=False)
        finally:
            self._inflight.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
