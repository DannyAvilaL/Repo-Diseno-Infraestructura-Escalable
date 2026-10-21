"""Pruebas sin red del laboratorio AZ-G con un transporte HTTP simulado.

Validan la lógica propia (orden de regiones, pausas por 429, clasificación de
errores, flujo batch). No sustituyen la prueba contra una suscripción real.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx2
import openai
import pytest
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "common"))

import batch_azure  # noqa: E402
from multiregion import AllRegionsFailed, MultiRegionChat, Region  # noqa: E402

MSG = [{"role": "user", "content": "hola"}]


def completion(text: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-1", "object": "chat.completion", "created": 0, "model": "gpt-5-mini",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    }


def client_with(handler: Any) -> OpenAI:
    return OpenAI(
        base_url="https://example.openai.azure.com/openai/v1/",
        api_key="token-de-prueba",
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def make_chat(primary: Any, secondary: Any, clock: Clock | None = None) -> tuple[MultiRegionChat, dict[str, int]]:
    calls = {"eastus2": 0, "swedencentral": 0}

    def counting(name: str, handler: Any) -> Any:
        def inner(request: httpx2.Request) -> httpx2.Response:
            calls[name] += 1
            return handler(request)
        return inner

    regions = [
        Region("eastus2", "https://a", "gpt-5-mini", client=client_with(counting("eastus2", primary))),
        Region("swedencentral", "https://b", "gpt-5-mini", client=client_with(counting("swedencentral", secondary))),
    ]
    return MultiRegionChat(regions, clock=clock or Clock()), calls


def ok(text: str) -> Any:
    return lambda request: httpx2.Response(200, json=completion(text))


def test_usa_la_primaria_si_esta_sana() -> None:
    chat, calls = make_chat(ok("A"), ok("B"))
    ans = chat.ask(MSG)
    assert (ans.text, ans.region, ans.attempts) == ("A", "eastus2", 1)
    assert calls == {"eastus2": 1, "swedencentral": 0}


def test_conmuta_ante_5xx() -> None:
    chat, _ = make_chat(lambda r: httpx2.Response(503, json={"error": {"message": "x"}}), ok("B"))
    ans = chat.ask(MSG)
    assert (ans.region, ans.attempts) == ("swedencentral", 2)


def test_conmuta_ante_error_de_conexion() -> None:
    def boom(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("sin red", request=request)

    chat, _ = make_chat(boom, ok("B"))
    assert chat.ask(MSG).region == "swedencentral"


def test_429_pausa_la_region_el_tiempo_indicado() -> None:
    clock = Clock()
    chat, calls = make_chat(
        lambda r: httpx2.Response(429, headers={"retry-after-ms": "20000"}, json={"error": {"message": "cuota"}}),
        ok("B"),
        clock,
    )
    chat.ask(MSG)
    chat.ask(MSG)
    assert calls["eastus2"] == 1  # la segunda solicitud no vuelve a la región pausada
    clock.t = 21
    chat.ask(MSG)
    assert calls["eastus2"] == 2


def test_4xx_no_conmuta() -> None:
    chat, calls = make_chat(lambda r: httpx2.Response(400, json={"error": {"message": "inválida"}}), ok("B"))
    with pytest.raises(openai.BadRequestError):
        chat.ask(MSG)
    assert calls["swedencentral"] == 0


def test_todas_fallan() -> None:
    fail = lambda r: httpx2.Response(500, json={"error": {"message": "x"}})  # noqa: E731
    chat, _ = make_chat(fail, fail)
    with pytest.raises(AllRegionsFailed) as exc:
        chat.ask(MSG)
    assert len(exc.value.errors) == 2


def test_envia_service_tier_y_max_completion_tokens() -> None:
    seen: dict[str, Any] = {}

    def capture(request: httpx2.Request) -> httpx2.Response:
        seen.update(json.loads(request.content))
        return httpx2.Response(200, json=completion("A"))

    chat, _ = make_chat(capture, ok("B"))
    chat.ask(MSG, service_tier="priority", max_completion_tokens=50)
    assert seen["service_tier"] == "priority" and seen["max_completion_tokens"] == 50
    assert seen["model"] == "gpt-5-mini"


# ---------------------------------------------------------------------- batch
class FakeBatchService:
    def __init__(self) -> None:
        self.uploaded: bytes = b""
        self.batch_body: dict[str, Any] = {}
        self.polls = 0

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        path = request.url.path
        if request.method == "POST" and path.endswith("/files"):
            self.uploaded = request.content
            return httpx2.Response(200, json={"id": "file-in", "object": "file", "bytes": 1, "created_at": 0,
                                               "filename": "lote.jsonl", "purpose": "batch", "status": "processed"})
        if request.method == "POST" and path.endswith("/batches"):
            self.batch_body = json.loads(request.content)
            return httpx2.Response(200, json=self._batch("validating"))
        if request.method == "GET" and path.endswith("/batches/batch-1"):
            self.polls += 1
            return httpx2.Response(200, json=self._batch("completed"))
        if path.endswith("/files/file-out/content"):
            line = {"custom_id": "PQRS0000001", "response": {"status_code": 200, "body": completion('{"tipo":"queja"}')}}
            return httpx2.Response(200, content=(json.dumps(line) + "\n").encode())
        return httpx2.Response(404, json={"error": {"message": path}})

    @staticmethod
    def _batch(status: str) -> dict[str, Any]:
        return {"id": "batch-1", "object": "batch", "endpoint": "/chat/completions", "input_file_id": "file-in",
                "completion_window": "24h", "status": status, "created_at": 0,
                "output_file_id": "file-out" if status == "completed" else None, "error_file_id": None,
                "request_counts": {"total": 3, "completed": 3 if status == "completed" else 0, "failed": 0}}


def test_flujo_batch_completo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(batch_azure, "DATA", tmp_path)
    monkeypatch.setattr(batch_azure, "LOTE", tmp_path / "lote.jsonl")
    monkeypatch.setattr(batch_azure, "ETIQUETAS", tmp_path / "etiquetas.jsonl")
    monkeypatch.setattr(batch_azure, "ESTADO", tmp_path / "estado.json")
    service = FakeBatchService()
    client = client_with(service)

    batch_azure.preparar(3, "mi-despliegue-batch")
    lineas = [json.loads(l) for l in (tmp_path / "lote.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {l["body"]["model"] for l in lineas} == {"mi-despliegue-batch"}  # mismo despliegue en todas las líneas

    batch_azure.enviar(client)
    assert b'name="purpose"' in service.uploaded and b"batch" in service.uploaded
    assert service.batch_body["completion_window"] == "24h"
    assert service.batch_body["input_file_id"] == "file-in"

    trabajo = batch_azure.estado(client, esperar=True, intervalo_s=0)
    assert trabajo.status == "completed" and service.polls == 1

    batch_azure.descargar(client)
    salida = (tmp_path / "salida_azure.jsonl").read_text()
    assert "PQRS0000001" in salida
