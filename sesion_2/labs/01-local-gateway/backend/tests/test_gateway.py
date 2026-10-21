"""Pruebas del gateway: circuit breaker, enrutamiento, failover y API online."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

import httpx
import pytest

from app.circuit_breaker import CircuitBreaker
from app.config import RegionConfig
from app.main import app
from app.region_client import RegionClient, RegionError, parse_retry_after
from app.router import NoRegionAvailable, Router
from conftest import FakeClock, Lab, make_settings

CHAT = {"messages": [{"role": "user", "content": "¿Cuándo inician las clases?"}]}


def sse_events(text: str) -> list[tuple[str, dict]]:
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


# ------------------------------------------------------------ circuit breaker
def make_breaker(clock: FakeClock, **kw: float) -> CircuitBreaker:
    params = {"failure_threshold": 3, "failure_window_s": 10, "open_s": 5, "max_open_s": 60} | kw
    return CircuitBreaker(clock=clock, **params)  # type: ignore[arg-type]


def test_breaker_abre_al_umbral_y_prueba_en_half_open(clock: FakeClock) -> None:
    b = make_breaker(clock)
    for _ in range(2):
        b.record_failure()
    assert b.state == "closed"
    b.record_failure()
    assert b.state == "open" and not b.allow_request()
    clock.advance(5)
    assert b.state == "half_open"
    assert b.allow_request() is True
    assert b.allow_request() is False  # solo una solicitud de prueba
    b.record_success()
    assert b.state == "closed"


def test_breaker_fallas_fuera_de_ventana_no_suman(clock: FakeClock) -> None:
    b = make_breaker(clock)
    b.record_failure()
    b.record_failure()
    clock.advance(11)
    b.record_failure()
    assert b.state == "closed"


def test_breaker_half_open_fallida_reabre(clock: FakeClock) -> None:
    b = make_breaker(clock, failure_threshold=1)
    b.record_failure()
    clock.advance(5)
    assert b.allow_request()
    b.record_failure()
    assert b.state == "open"


def test_breaker_respeta_retry_after_con_tope(clock: FakeClock) -> None:
    b = make_breaker(clock)
    b.record_failure(retry_after_s=30)
    assert b.state == "open" and b.open_remaining_s() == pytest.approx(30)
    b.record_success()
    b.record_failure(retry_after_s=10_000)
    assert b.open_remaining_s() == pytest.approx(60)  # max_open_s


def test_parse_retry_after() -> None:
    assert parse_retry_after(httpx.Headers({"retry-after-ms": "1500"})) == 1.5
    assert parse_retry_after(httpx.Headers({"Retry-After": "7"})) == 7
    assert parse_retry_after(httpx.Headers({"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})) is None
    assert parse_retry_after(httpx.Headers({})) is None


# -------------------------------------------------------------- enrutamiento
async def test_prioridad_usa_region_primaria(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    r = await client.post("/v1/chat", json=CHAT)
    assert r.status_code == 200
    m = r.json()["metrics"]
    assert m["region"] == "region-a" and m["attempts"] == 1 and m["failover"] is False
    assert lab.calls == {"region-a": 1, "region-b": 0}


async def test_failover_cuando_la_primaria_cae(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    await lab.set_mode("region-a", mode="down")
    r = await client.post("/v1/chat", json=CHAT)
    assert r.status_code == 200
    m = r.json()["metrics"]
    assert m["region"] == "region-b" and m["attempts"] == 2 and m["failover"] is True
    assert "[region-b]" in r.json()["content"]


async def test_circuito_abierto_evita_reintentar_la_region(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    await lab.set_mode("region-a", mode="down")
    for _ in range(lab.settings.cb_failure_threshold):
        await client.post("/v1/chat", json=CHAT)
    calls_a = lab.calls["region-a"]
    r = await client.post("/v1/chat", json=CHAT)
    assert r.json()["metrics"]["attempts"] == 1  # va directo a la secundaria
    assert lab.calls["region-a"] == calls_a
    status = (await client.get("/v1/regions")).json()
    assert status["regions"][0]["circuit"] == "open"


async def test_429_con_retry_after_abre_el_circuito(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    await lab.set_mode("region-a", mode="throttle", retry_after_s=40)
    await client.post("/v1/chat", json=CHAT)
    region_a = (await client.get("/v1/regions")).json()["regions"][0]
    assert region_a["circuit"] == "open"
    assert region_a["circuit_open_remaining_s"] == pytest.approx(40, abs=0.5)
    lab.clock.advance(41)
    await lab.set_mode("region-a", mode="healthy")
    r = await client.post("/v1/chat", json=CHAT)
    assert r.json()["metrics"]["region"] == "region-a"  # la prueba en half-open cerró el circuito


async def test_region_lenta_supera_timeout_de_primer_byte(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    await lab.set_mode("region-a", mode="slow", slow_ms=3000)
    r = await client.post("/v1/chat", json=CHAT)
    assert r.json()["metrics"]["region"] == "region-b"


async def test_round_robin_alterna_regiones(lab_factory: Callable[..., Lab]) -> None:
    lab = lab_factory(routing="round_robin")
    served = []
    for _ in range(4):
        state, body, _ = await lab.router.complete([{"role": "user", "content": "hola"}], max_tokens=10, temperature=0)
        served.append(state.name)
    assert set(served) == {"region-a", "region-b"}
    assert served[0] != served[1]


async def test_sin_regiones_devuelve_503_y_evento_error(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    await lab.set_mode("region-a", mode="down")
    await lab.set_mode("region-b", mode="down")
    r = await client.post("/v1/chat", json=CHAT)
    assert r.status_code == 503
    r = await client.post("/v1/chat/stream", json=CHAT)
    events = sse_events(r.text)
    assert events[-1][0] == "error"


async def test_error_4xx_no_conmuta(tmp_path, clock: FakeClock) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"message": "solicitud inválida"}})

    settings = make_settings(tmp_path)
    clients = [
        RegionClient(cfg, connect_timeout_s=1, first_byte_timeout_s=1, read_timeout_s=1, health_timeout_s=1,
                     client=httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=str(cfg.base_url)))
        for cfg in settings.regions
    ]
    router = Router(settings, clients=clients, clock=clock)
    with pytest.raises(RegionError) as exc:
        await router.complete([{"role": "user", "content": "x"}], max_tokens=5, temperature=0)
    assert exc.value.status_code == 400
    assert router.regions["region-b"].requests == 0
    assert router.regions["region-a"].breaker.state == "closed"


async def test_presupuesto_de_intentos(lab_factory: Callable[..., Lab]) -> None:
    lab = lab_factory(max_attempts=1)
    await lab.set_mode("region-a", mode="down")
    with pytest.raises(NoRegionAvailable):
        await lab.router.complete([{"role": "user", "content": "x"}], max_tokens=5, temperature=0)
    assert lab.calls["region-b"] == 0


# ----------------------------------------------------------------- streaming
async def test_stream_informa_region_y_metricas(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    await lab.set_mode("region-a", mode="down")
    r = await client.post("/v1/chat/stream", json=CHAT)
    events = sse_events(r.text)
    kinds = [e for e, _ in events]
    assert kinds[0] == "region" and kinds[-2:] == ["metrics", "done"]
    assert events[0][1] == {"name": "region-b", "attempts": 2, "failover": True}
    metrics = events[-2][1]
    assert metrics["region"] == "region-b" and metrics["completion_tokens"] > 0
    assert lab.router.online_inflight == 0
    assert all(s.inflight == 0 for s in lab.router.regions.values())


# ------------------------------------------------------- salud y administración
async def test_health_check_y_readyz(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    await lab.router.check_health_once()
    assert (await client.get("/readyz")).json()["available_regions"] == ["region-a", "region-b"]
    await lab.set_mode("region-a", mode="down")
    await lab.router.check_health_once()
    assert [r.name for r in lab.router.candidates()] == ["region-b", "region-a"]  # la no sana queda al final
    await lab.set_mode("region-b", mode="down")
    await lab.router.check_health_once()
    r = await client.get("/readyz")
    assert r.status_code == 503 and r.json()["status"] == "degraded"


async def test_health_check_detecta_modelo_inexistente(tmp_path, clock: FakeClock) -> None:
    lab = Lab(tmp_path, clock, regions=[RegionConfig(name="region-a", base_url="http://region-a/v1", model="otro")])
    await lab.router.check_health_once()
    state = lab.router.regions["region-a"]
    assert state.healthy is False and "otro" in (state.health_detail or "")


async def test_admin_deshabilita_region_y_exige_token(lab_factory: Callable[..., Lab]) -> None:
    lab = lab_factory(admin_token="secreto-de-prueba")
    from app.config import get_settings

    app.state.router, app.state.batch = lab.router, lab.batch
    app.dependency_overrides[get_settings] = lambda: lab.settings
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gw") as client:
            assert (await client.post("/admin/regions/region-a/disable")).status_code == 401
            r = await client.post("/admin/regions/region-a/disable", headers={"X-Admin-Token": "secreto-de-prueba"})
            assert r.status_code == 200
            assert (await client.post("/v1/chat", json=CHAT)).json()["metrics"]["region"] == "region-b"
            r = await client.post("/admin/regions/region-z/disable", headers={"X-Admin-Token": "secreto-de-prueba"})
            assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


async def test_limite_de_entrada(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    _, client = gateway
    big = {"messages": [{"role": "user", "content": "x" * 5000}]}
    assert (await client.post("/v1/chat", json=big)).status_code == 413


async def test_logs_sin_contenido_de_conversacion(gateway: tuple[Lab, httpx.AsyncClient], caplog: pytest.LogCaptureFixture) -> None:
    _, client = gateway
    secreto = "Mi número de documento es 123456789"
    with caplog.at_level(logging.INFO):
        await client.post("/v1/chat", json={"messages": [{"role": "user", "content": secreto}]})
    assert secreto not in caplog.text
    assert "chat_completado" in caplog.text
