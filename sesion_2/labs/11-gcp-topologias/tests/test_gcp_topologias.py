"""Pruebas sin red de GCP-D con clientes simulados (google-genai y Cloud Storage)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from google.genai import errors, types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "common"))

import batch_gemini  # noqa: E402
from multiregion_gcp import AllLocationsFailed, Location, MultiLocationGemini, build_client  # noqa: E402


class FakeModels:
    def __init__(self, behavior: Any) -> None:
        self.behavior = behavior
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, *, model: str, contents: str, config: types.GenerateContentConfig) -> Any:
        self.calls.append({"model": model, "contents": contents, "config": config})
        if isinstance(self.behavior, Exception):
            raise self.behavior
        usage = types.GenerateContentResponseUsageMetadata(prompt_token_count=5, candidates_token_count=3)
        return SimpleNamespace(text=self.behavior, usage_metadata=usage)


def fake_client(behavior: Any) -> SimpleNamespace:
    return SimpleNamespace(models=FakeModels(behavior))


def api_error(code: int) -> errors.APIError:
    return errors.APIError(code, {"error": {"code": code, "message": "x", "status": "X"}})


class Clock:
    t = 0.0

    def __call__(self) -> float:
        return self.t


def gemini(primary: Any, secondary: Any, clock: Clock | None = None) -> MultiLocationGemini:
    return MultiLocationGemini(
        "modelo-de-prueba",
        [Location("us-central1", fake_client(primary)), Location("us-east4", fake_client(secondary))],
        clock=clock or Clock(),
    )


def test_primaria_sana() -> None:
    ans = gemini("A", "B").ask("hola", system="s")
    assert (ans.text, ans.location, ans.attempts) == ("A", "us-central1", 1)
    assert ans.usage["prompt_token_count"] == 5


@pytest.mark.parametrize("code", [429, 500, 503])
def test_conmuta_ante_errores_reintentables(code: int) -> None:
    ans = gemini(api_error(code), "B").ask("hola", system="s")
    assert (ans.location, ans.attempts) == ("us-east4", 2)


def test_conmuta_ante_error_de_transporte() -> None:
    ans = gemini(httpx.ConnectError("sin red"), "B").ask("hola", system="s")
    assert ans.location == "us-east4"


def test_4xx_no_conmuta() -> None:
    g = gemini(api_error(400), "B")
    with pytest.raises(errors.APIError):
        g.ask("hola", system="s")
    assert g.locations[1].client.models.calls == []


def test_pausa_y_recuperacion() -> None:
    clock = Clock()
    g = gemini(api_error(429), "B", clock)
    g.ask("x", system="s")
    g.ask("x", system="s")
    assert len(g.locations[0].client.models.calls) == 1
    clock.t = 31
    g.ask("x", system="s")
    assert len(g.locations[0].client.models.calls) == 2


def test_todas_fallan_y_service_tier() -> None:
    g = gemini(api_error(503), api_error(503))
    with pytest.raises(AllLocationsFailed):
        g.ask("x", system="s", service_tier="flex")
    config = g.locations[0].client.models.calls[0]["config"]
    assert config.service_tier == types.ServiceTier.FLEX
    assert config.system_instruction == "s"


def test_build_client_desactiva_reintentos_del_sdk() -> None:
    client = build_client("proyecto", "us-central1")
    opts = client._api_client._http_options
    assert opts.retry_options.attempts == 1 and opts.timeout == 30_000


# ---------------------------------------------------------------------- batch
class FakeBlob:
    def __init__(self, store: dict[str, bytes], name: str) -> None:
        self.store, self.name = store, name

    def upload_from_filename(self, path: str, content_type: str) -> None:
        self.store[self.name] = Path(path).read_bytes()

    def download_as_bytes(self) -> bytes:
        return self.store[self.name]


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def bucket(self, name: str) -> SimpleNamespace:
        return SimpleNamespace(blob=lambda path: FakeBlob(self.objects, path))

    def list_blobs(self, bucket: str, prefix: str) -> list[FakeBlob]:
        return [FakeBlob(self.objects, k) for k in self.objects if k.startswith(prefix)]


class FakeBatches:
    def __init__(self) -> None:
        self.created: dict[str, Any] = {}

    def create(self, *, model: str, src: str, config: types.CreateBatchJobConfig) -> types.BatchJob:
        self.created = {"model": model, "src": src, "dest": config.dest}
        return types.BatchJob(name="projects/p/locations/us-central1/batchPredictionJobs/1", state=types.JobState.JOB_STATE_PENDING)

    def get(self, *, name: str) -> types.BatchJob:
        return types.BatchJob(
            name=name,
            state=types.JobState.JOB_STATE_SUCCEEDED,
            dest=types.BatchJobDestination(gcs_uri="gs://bucket-curso/pqrs/salida/prediction-model-1"),
        )


def test_flujo_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(batch_gemini, "DATA", tmp_path)
    monkeypatch.setattr(batch_gemini, "ESTADO", tmp_path / "estado.json")
    storage = FakeStorage()
    client = SimpleNamespace(batches=FakeBatches())

    uri = batch_gemini.preparar(storage, "bucket-curso", 3)
    assert uri == "gs://bucket-curso/pqrs/entrada.jsonl"
    primera = json.loads(storage.objects["pqrs/entrada.jsonl"].decode().splitlines()[0])
    assert set(primera) == {"request"}

    batch_gemini.enviar(client, "bucket-curso", "modelo-de-prueba")
    assert client.batches.created == {
        "model": "modelo-de-prueba",
        "src": "gs://bucket-curso/pqrs/entrada.jsonl",
        "dest": "gs://bucket-curso/pqrs/salida/",
    }
    assert batch_gemini._state_name(batch_gemini.estado(client, esperar=True, intervalo_s=0)) == "JOB_STATE_SUCCEEDED"

    storage.objects["pqrs/salida/prediction-model-1/predictions.jsonl"] = b'{"request": {}, "response": {}}\n'
    salida = batch_gemini.descargar(client, storage)
    assert salida.read_text().count("\n") == 1
