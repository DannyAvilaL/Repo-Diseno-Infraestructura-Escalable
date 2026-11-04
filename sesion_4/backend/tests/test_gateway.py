import asyncio

import httpx
import pytest

from .conftest import BODY, build, make_ollama

pytestmark = pytest.mark.anyio


async def test_healthz_no_depende_de_ollama():
    _, c = build(make_ollama(fail=True))
    r = await c.get("/healthz")
    assert r.status_code == 200 and r.json()["status"] == "ok"


async def test_readyz_ok_y_no_listo_si_falta_el_modelo():
    _, c = build(make_ollama())
    assert (await c.get("/readyz")).status_code == 200
    _, c2 = build(make_ollama(models=["otro-modelo"]))
    assert (await c2.get("/readyz")).status_code == 503


async def test_chat_no_streaming_devuelve_contenido_uso_y_tiempos():
    _, c = build(make_ollama())
    r = await c.post("/v1/chat", json=BODY)
    assert r.status_code == 200
    data = r.json()
    assert data["content"] == "Hola, mundo"
    assert data["usage"] == {"input_tokens": 7, "output_tokens": 3}
    assert data["timings"]["ttft_s"] is not None and data["timings"]["e2e_s"] >= 0


async def test_chat_streaming_emite_eventos_sse():
    _, c = build(make_ollama())
    r = await c.post("/v1/chat", json={**BODY, "stream": True})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert "event: token" in r.text and "event: done" in r.text


async def test_validacion_rechaza_mensajes_vacios_y_roles_invalidos():
    _, c = build(make_ollama())
    assert (await c.post("/v1/chat", json={"messages": []})).status_code == 422
    bad = {"messages": [{"role": "tool", "content": "x"}]}
    assert (await c.post("/v1/chat", json=bad)).status_code == 422


async def test_api_key_requerida_cuando_esta_configurada():
    _, c = build(make_ollama(), api_key="s3cret")
    assert (await c.post("/v1/chat", json=BODY)).status_code == 401
    assert (await c.post("/v1/chat", json=BODY, headers={"X-API-Key": "mal"})).status_code == 401
    assert (await c.post("/v1/chat", json=BODY, headers={"X-API-Key": "s3cret"})).status_code == 200


async def test_upstream_caido_devuelve_502():
    _, c = build(make_ollama(fail=True))
    r = await c.post("/v1/chat", json=BODY)
    assert r.status_code == 502


async def test_cola_llena_aplica_load_shedding_429():
    """1 slot, cola 0: la segunda solicitud simultánea se rechaza de inmediato."""
    _, c = build(make_ollama(delay=0.3), max_concurrency=1, max_queue=0)
    r1, r2 = await asyncio.gather(c.post("/v1/chat", json=BODY), c.post("/v1/chat", json=BODY))
    codes = sorted([r1.status_code, r2.status_code])
    assert codes == [200, 429]
    rejected = r1 if r1.status_code == 429 else r2
    assert rejected.headers["retry-after"] == "5"


async def test_timeout_en_cola_devuelve_503():
    _, c = build(make_ollama(delay=0.5), max_concurrency=1, max_queue=5, queue_timeout_s=0.1)
    r1, r2 = await asyncio.gather(c.post("/v1/chat", json=BODY), c.post("/v1/chat", json=BODY))
    assert sorted([r1.status_code, r2.status_code]) == [200, 503]


async def test_cola_acotada_sirve_a_todos_si_hay_espera_suficiente():
    _, c = build(make_ollama(delay=0.05), max_concurrency=1, max_queue=5, queue_timeout_s=5)
    rs = await asyncio.gather(*[c.post("/v1/chat", json=BODY) for _ in range(4)])
    assert [r.status_code for r in rs] == [200] * 4
    assert max(r.json()["timings"]["queue_wait_s"] for r in rs) > 0.05  # hubo cola real


async def test_metricas_exponen_senales_de_autoscaling_y_slots_se_liberan():
    _, c = build(make_ollama())
    await c.post("/v1/chat", json=BODY)
    await c.post("/v1/chat", json={**BODY, "stream": True})
    text = (await c.get("/metrics")).text
    for name in ("llm_gateway_queue_depth", "llm_gateway_in_flight", "llm_gateway_ttft_seconds_count",
                 "llm_gateway_output_tokens_total"):
        assert name in text
    assert "llm_gateway_in_flight 0.0" in text and "llm_gateway_queue_depth 0.0" in text
    assert 'llm_gateway_requests_total{outcome="ok"} 2.0' in text
