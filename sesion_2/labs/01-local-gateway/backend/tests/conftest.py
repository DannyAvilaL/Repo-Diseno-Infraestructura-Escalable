"""Fixtures: dos regiones simuladas conectadas en memoria (sin red ni puertos)."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT.parent / "common"))

from mock_region import create_app as create_region  # noqa: E402

from app.batch import BatchProcessor, BatchStore  # noqa: E402
from app.config import RegionConfig, Settings, get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.region_client import RegionClient  # noqa: E402
from app.router import Router  # noqa: E402


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_settings(tmp_path: Path, **overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "regions": [
            RegionConfig(name="region-a", base_url="http://region-a/v1", model="simulado", priority=1),
            RegionConfig(name="region-b", base_url="http://region-b/v1", model="simulado", priority=2),
        ],
        "batch_dir": tmp_path / "batches",
        "first_byte_timeout_s": 1.0,
        "batch_retry_base_s": 0.0,
        "health_interval_s": 3600,
    }
    base.update(overrides)
    return Settings(**base)


class Lab:
    """Agrupa regiones simuladas, router, procesador batch y cliente HTTP del gateway."""

    def __init__(self, tmp_path: Path, clock: FakeClock, **overrides: Any) -> None:
        self.settings = make_settings(tmp_path, **overrides)
        self.sims = {
            r.name: create_region(r.name, tpot_ms=1, prefill_ms=1, prefill_ms_per_1k_chars=0, seed=1)
            for r in self.settings.regions
        }
        self.calls: dict[str, int] = {name: 0 for name in self.sims}
        clients = []
        for cfg in self.settings.regions:
            transport = self._counting_transport(cfg.name, httpx.ASGITransport(app=self.sims[cfg.name]))
            clients.append(
                RegionClient(
                    cfg,
                    connect_timeout_s=1,
                    first_byte_timeout_s=self.settings.first_byte_timeout_s,
                    read_timeout_s=5,
                    health_timeout_s=1,
                    client=httpx.AsyncClient(transport=transport, base_url=str(cfg.base_url).rstrip("/")),
                )
            )
        self.clock = clock
        self.router = Router(self.settings, clients=clients, clock=clock)
        self.store = BatchStore(self.settings.batch_dir)
        self.batch = BatchProcessor(self.settings, self.router, self.store, clock=clock)

    def _counting_transport(self, name: str, inner: httpx.AsyncBaseTransport) -> httpx.AsyncBaseTransport:
        lab = self

        class Counting(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
                if request.url.path.endswith("/chat/completions"):
                    lab.calls[name] += 1
                return await inner.handle_async_request(request)

        return Counting()

    async def set_mode(self, region: str, **state: Any) -> None:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.sims[region]), base_url="http://sim") as c:
            r = await c.post("/admin/state", json=state)
            r.raise_for_status()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def lab_factory(tmp_path: Path, clock: FakeClock) -> Callable[..., Lab]:
    def factory(**overrides: Any) -> Lab:
        return Lab(tmp_path, clock, **overrides)

    return factory


@pytest.fixture
async def gateway(lab_factory: Callable[..., Lab]) -> AsyncIterator[tuple[Lab, httpx.AsyncClient]]:
    lab = lab_factory()
    app.state.router, app.state.batch = lab.router, lab.batch
    app.dependency_overrides[get_settings] = lambda: lab.settings
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway") as client:
        yield lab, client
    app.dependency_overrides.clear()
