"""Pruebas del caché: TTL, LRU, aislamiento por tenant y single-flight."""

from __future__ import annotations

import asyncio

from serverless_llm.cache import ResponseCache, make_cache_key


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _key(tenant: str = "a", prompt: str = "hola") -> str:
    return make_cache_key(
        tenant=tenant, model="m", prompt=prompt, system=None, temperature=0.0, max_tokens=10
    )


async def test_hit_after_miss() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_s=10, max_entries=10)
    calls = 0

    async def compute() -> str:
        nonlocal calls
        calls += 1
        return "respuesta"

    first = await cache.get_or_compute(_key(), compute, cacheable=True)
    second = await cache.get_or_compute(_key(), compute, cacheable=True)
    assert (first.hit, second.hit) == (False, True)
    assert calls == 1
    assert cache.stats.hit_ratio == 0.5


async def test_ttl_expiration() -> None:
    clock = FakeClock()
    cache: ResponseCache[str] = ResponseCache(ttl_s=10, max_entries=10, clock=clock)

    async def compute() -> str:
        return "x"

    await cache.get_or_compute(_key(), compute, cacheable=True)
    clock.now = 11
    outcome = await cache.get_or_compute(_key(), compute, cacheable=True)
    assert outcome.hit is False
    assert cache.stats.expirations == 1


async def test_lru_eviction() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_s=100, max_entries=2)

    async def compute() -> str:
        return "x"

    for p in ("a", "b", "c"):
        await cache.get_or_compute(_key(prompt=p), compute, cacheable=True)
    assert len(cache) == 2
    assert cache.stats.evictions == 1
    assert (await cache.get_or_compute(_key(prompt="a"), compute, cacheable=True)).hit is False


def test_key_isolated_by_tenant() -> None:
    assert _key("a") != _key("b")


def test_key_normalizes_outer_whitespace() -> None:
    assert _key(prompt="hola") == _key(prompt="  hola \n")


async def test_not_cacheable_bypasses_cache() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_s=10, max_entries=10)
    calls = 0

    async def compute() -> str:
        nonlocal calls
        calls += 1
        return "x"

    for _ in range(3):
        outcome = await cache.get_or_compute(_key(), compute, cacheable=False)
        assert outcome.hit is False
    assert calls == 3


async def test_single_flight_coalesces_concurrent_requests() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_s=10, max_entries=10)
    calls = 0

    async def compute() -> str:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return "unica"

    results = await asyncio.gather(
        *(cache.get_or_compute(_key(), compute, cacheable=True) for _ in range(10))
    )
    assert calls == 1
    assert sum(r.coalesced for r in results) == 9
    assert {r.value for r in results} == {"unica"}


async def test_failure_is_not_cached_and_propagates_to_waiters() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_s=10, max_entries=10)

    async def boom() -> str:
        await asyncio.sleep(0.02)
        raise RuntimeError("fallo")

    results = await asyncio.gather(
        *(cache.get_or_compute(_key(), boom, cacheable=True) for _ in range(3)),
        return_exceptions=True,
    )
    assert all(isinstance(r, RuntimeError) for r in results)
    assert len(cache) == 0
