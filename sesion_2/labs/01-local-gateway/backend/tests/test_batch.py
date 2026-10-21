"""Pruebas de la inferencia por lotes: validación, ciclo de vida y prioridad online."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

import lote_pqrs as lp
from app.batch import BatchValidationError, parse_batch_input
from conftest import Lab


def jsonl(lines: list[dict]) -> bytes:
    return ("\n".join(json.dumps(line, ensure_ascii=False) for line in lines) + "\n").encode("utf-8")


def lote(n: int = 10) -> tuple[list[lp.PQRS], bytes]:
    items = lp.generar_pqrs(n, proporcion_inyeccion=0.0)
    return items, jsonl(lp.a_openai_batch(items, "simulado"))


# ----------------------------------------------------------------- validación
@pytest.mark.parametrize(
    ("raw", "fragmento"),
    [
        (b"\xef\xbb\xbf" + jsonl(lp.a_openai_batch(lp.generar_pqrs(1), "m")), "BOM"),
        (b"{no es json}\n", "JSON inválido"),
        (b"", "no contiene solicitudes"),
        (jsonl([{"custom_id": "a", "method": "GET", "url": "/v1/chat/completions", "body": {"messages": []}}]), "POST"),
        (jsonl([{"custom_id": "a", "method": "POST", "url": "/v1/embeddings", "body": {}}]), "url"),
        (jsonl([{"custom_id": "a", "method": "POST", "url": "/v1/chat/completions", "body": {"messages": [{"role": "tool"}]}}]), "role"),
    ],
)
def test_validacion_rechaza_entradas_invalidas(raw: bytes, fragmento: str) -> None:
    with pytest.raises(BatchValidationError) as exc:
        parse_batch_input(raw, max_requests=100, max_bytes=1_000_000)
    assert fragmento in " ".join(exc.value.errors)


def test_validacion_detecta_duplicados_y_maximo() -> None:
    linea = lp.a_openai_batch(lp.generar_pqrs(1), "m")[0]
    with pytest.raises(BatchValidationError, match="duplicado"):
        parse_batch_input(jsonl([linea, linea]), max_requests=100, max_bytes=1_000_000)
    _, raw = lote(5)
    with pytest.raises(BatchValidationError, match="máximo"):
        parse_batch_input(raw, max_requests=3, max_bytes=1_000_000)


# --------------------------------------------------------------- ciclo de vida
async def test_lote_completo_por_api(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    items, raw = lote(12)
    r = await client.post("/v1/batches?description=pqrs", content=raw, headers={"Content-Type": "application/jsonl"})
    assert r.status_code == 202
    job = r.json()
    assert job["status"] == "validating" and job["request_counts"]["total"] == 12

    await lab.batch.process(job["id"])
    job = (await client.get(f"/v1/batches/{job['id']}")).json()
    assert job["status"] == "completed"
    assert job["request_counts"] == {"total": 12, "completed": 12, "failed": 0}

    out = (await client.get(f"/v1/batches/{job['id']}/output")).text.splitlines()
    resultados = {
        json.loads(l)["custom_id"]: json.loads(l)["response"]["body"]["choices"][0]["message"]["content"] for l in out
    }
    resumen = lp.resumir(resultados, items)
    assert resumen["json_validos"] == 12 and resumen["exactitud_area"] == 1.0
    assert (await client.get(f"/v1/batches/{job['id']}/errors")).text == ""
    assert [j["id"] for j in (await client.get("/v1/batches")).json()["data"]] == [job["id"]]


async def test_lote_invalido_responde_400_y_queda_failed(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    r = await client.post("/v1/batches", content=b"{malo}\n")
    assert r.status_code == 400
    assert "JSON inválido" in json.dumps(r.json(), ensure_ascii=False)
    assert lab.store.list()[0].status == "failed"


async def test_lote_conmuta_si_la_primaria_cae(lab_factory: Callable[..., Lab]) -> None:
    lab = lab_factory()
    await lab.set_mode("region-a", mode="down")
    _, raw = lote(8)
    job = lab.batch.submit(raw)
    job = await lab.batch.process(job.id)
    assert job.status == "completed"
    assert job.regions_used == {"region-b": 8}


async def test_lote_sin_regiones_registra_errores(lab_factory: Callable[..., Lab]) -> None:
    lab = lab_factory(batch_max_retries=1)
    await lab.set_mode("region-a", mode="down")
    await lab.set_mode("region-b", mode="down")
    _, raw = lote(3)
    job = await lab.batch.process(lab.batch.submit(raw).id)
    assert job.status == "completed"  # como en los servicios gestionados: completed con solicitudes fallidas
    assert job.request_counts.failed == 3
    errores = lab.store.error_path(job.id).read_text().splitlines()
    assert json.loads(errores[0])["error"]["code"] == "regions_unavailable"


async def test_cancelacion_antes_de_iniciar(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    lab, client = gateway
    _, raw = lote(4)
    job = (await client.post("/v1/batches", content=raw)).json()
    r = await client.post(f"/v1/batches/{job['id']}/cancel")
    assert r.json()["status"] == "cancelling"
    final = await lab.batch.process(job["id"])
    assert final.status == "cancelled" and final.request_counts.completed == 0
    assert (await client.post(f"/v1/batches/{job['id']}/cancel")).status_code == 409


async def test_ventana_vencida_marca_expired(lab_factory: Callable[..., Lab]) -> None:
    lab = lab_factory(batch_completion_window_s=60)
    _, raw = lote(3)
    job = lab.batch.submit(raw)
    lab.clock.advance(61)
    final = await lab.batch.process(job.id)
    assert final.status == "expired" and final.request_counts.completed == 0


async def test_lote_cede_capacidad_a_lo_online(lab_factory: Callable[..., Lab]) -> None:
    lab = lab_factory(batch_yield_online_inflight=1)
    lab.router.online_inflight = 1
    esperas: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        esperas.append(seconds)
        lab.router.online_inflight = 0  # termina la solicitud interactiva

    lab.batch._sleep = fake_sleep  # type: ignore[assignment]
    _, raw = lote(2)
    final = await lab.batch.process(lab.batch.submit(raw).id)
    assert final.status == "completed"
    assert esperas, "el lote debió esperar a que terminara la solicitud online"


async def test_reanudacion_no_repite_solicitudes(lab_factory: Callable[..., Lab]) -> None:
    lab = lab_factory()
    _, raw = lote(6)
    job = lab.batch.submit(raw)
    # Simula un reinicio a mitad del trabajo: dos solicitudes ya resueltas en disco.
    for line in lab.store.read_input(job.id)[:2]:
        lab.store.append(lab.store.output_path(job.id), {"custom_id": line["custom_id"], "response": {}, "error": None})
    job.status = "in_progress"
    lab.store.save(job)
    final = await lab.batch.process(job.id)
    assert final.status == "completed" and final.request_counts.completed == 6
    assert lab.calls["region-a"] == 4


async def test_ids_manipulados_no_acceden_al_disco(gateway: tuple[Lab, httpx.AsyncClient]) -> None:
    _, client = gateway
    assert (await client.get("/v1/batches/..%2F..%2Fetc%2Fpasswd")).status_code == 404
    assert (await client.get("/v1/batches/batch_..x/output")).status_code == 404
