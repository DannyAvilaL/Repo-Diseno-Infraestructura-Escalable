"""Pruebas sin red de AWS-E con botocore Stubber (valida parámetros contra el modelo del servicio)."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "common"))

import batch_bedrock  # noqa: E402
from multiregion_aws import AllRegionsFailed, MultiRegionBedrock, Target, runtime_client  # noqa: E402


def converse_ok(text: str, tier: str | None = None) -> dict[str, Any]:
    resp: dict[str, Any] = {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
        "usage": {"inputTokens": 5, "outputTokens": 3, "totalTokens": 8},
        "metrics": {"latencyMs": 10},
    }
    if tier:
        resp["serviceTier"] = {"type": tier}
    return resp


@pytest.fixture
def two_regions(monkeypatch: pytest.MonkeyPatch) -> tuple[MultiRegionBedrock, Stubber, Stubber]:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "prueba")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "prueba")
    a = runtime_client("us-east-1")
    b = runtime_client("us-west-2")
    sa, sb = Stubber(a), Stubber(b)
    sa.activate()
    sb.activate()

    class Clock:
        t = 0.0

        def __call__(self) -> float:
            return self.t

    chat = MultiRegionBedrock(
        [Target("us-east-1", "amazon.nova-lite-v1:0", a), Target("us-west-2", "us.amazon.nova-lite-v1:0", b)],
        clock=Clock(),
    )
    return chat, sa, sb


def test_primaria_sana(two_regions: tuple[MultiRegionBedrock, Stubber, Stubber]) -> None:
    chat, sa, _ = two_regions
    sa.add_response("converse", converse_ok("A"), {
        "modelId": "amazon.nova-lite-v1:0", "system": [{"text": "s"}],
        "messages": [{"role": "user", "content": [{"text": "hola"}]}],
        "inferenceConfig": {"maxTokens": 800, "temperature": 0.2},
    })
    ans = chat.ask("hola", system="s")
    assert (ans.text, ans.region, ans.attempts) == ("A", "us-east-1", 1)
    sa.assert_no_pending_responses()


@pytest.mark.parametrize("code,status", [("ThrottlingException", 429), ("ServiceUnavailableException", 503), ("ModelNotReadyException", 429)])
def test_conmuta_ante_errores_reintentables(two_regions: tuple[MultiRegionBedrock, Stubber, Stubber], code: str, status: int) -> None:
    chat, sa, sb = two_regions
    sa.add_client_error("converse", service_error_code=code, http_status_code=status)
    sb.add_response("converse", converse_ok("B"), {"modelId": "us.amazon.nova-lite-v1:0", "system": ANY, "messages": ANY, "inferenceConfig": ANY})
    ans = chat.ask("hola", system="s")
    assert (ans.region, ans.model_id, ans.attempts) == ("us-west-2", "us.amazon.nova-lite-v1:0", 2)


def test_validacion_no_conmuta(two_regions: tuple[MultiRegionBedrock, Stubber, Stubber]) -> None:
    chat, sa, sb = two_regions
    sa.add_client_error("converse", service_error_code="ValidationException", http_status_code=400)
    with pytest.raises(Exception, match="ValidationException"):
        chat.ask("hola", system="s")
    sb.assert_no_pending_responses()


def test_error_de_conexion_conmuta(two_regions: tuple[MultiRegionBedrock, Stubber, Stubber], monkeypatch: pytest.MonkeyPatch) -> None:
    chat, _, sb = two_regions

    def boom(**kwargs: Any) -> Any:
        raise EndpointConnectionError(endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com")

    monkeypatch.setattr(chat.targets[0].client, "converse", boom)
    sb.add_response("converse", converse_ok("B"), {"modelId": ANY, "system": ANY, "messages": ANY, "inferenceConfig": ANY})
    assert chat.ask("hola", system="s").region == "us-west-2"


def test_service_tier_y_todas_fallan(two_regions: tuple[MultiRegionBedrock, Stubber, Stubber]) -> None:
    chat, sa, sb = two_regions
    sa.add_response("converse", converse_ok("A", "flex"), {
        "modelId": ANY, "system": ANY, "messages": ANY, "inferenceConfig": ANY, "serviceTier": {"type": "flex"},
    })
    assert chat.ask("hola", system="s", service_tier="flex").service_tier == "flex"
    chat.targets[0].paused_until = chat.targets[1].paused_until = 0
    sa.add_client_error("converse", service_error_code="InternalServerException", http_status_code=500)
    sb.add_client_error("converse", service_error_code="InternalServerException", http_status_code=500)
    with pytest.raises(AllRegionsFailed):
        chat.ask("hola", system="s")


# ---------------------------------------------------------------------- batch
def test_flujo_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "prueba")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "prueba")
    monkeypatch.setattr(batch_bedrock, "DATA", tmp_path)
    monkeypatch.setattr(batch_bedrock, "ESTADO", tmp_path / "estado.json")
    s3 = boto3.client("s3", region_name="us-east-1")
    bedrock = boto3.client("bedrock", region_name="us-east-1")
    subidos: dict[str, bytes] = {}
    monkeypatch.setattr(s3, "upload_file", lambda f, b, k: subidos.__setitem__(k, Path(f).read_bytes()))

    with pytest.raises(SystemExit, match="al menos 100"):
        batch_bedrock.preparar(s3, "bucket-curso", 50)
    uri = batch_bedrock.preparar(s3, "bucket-curso", 120)
    assert uri == "s3://bucket-curso/pqrs/entrada/"
    primera = json.loads(subidos["pqrs/entrada/lote.jsonl"].decode().splitlines()[0])
    assert primera["recordId"] == "PQRS0000001" and "modelInput" in primera

    arn = "arn:aws:bedrock:us-east-1:111122223333:model-invocation-job/abc123"
    with Stubber(bedrock) as sb:
        sb.add_response("create_model_invocation_job", {"jobArn": arn}, {
            "jobName": ANY, "clientRequestToken": ANY,
            "roleArn": "arn:aws:iam::111122223333:role/bedrock-batch-pqrs",
            "modelId": "amazon.nova-lite-v1:0", "modelInvocationType": "Converse",
            "inputDataConfig": {"s3InputDataConfig": {"s3Uri": "s3://bucket-curso/pqrs/entrada/"}},
            "outputDataConfig": {"s3OutputDataConfig": {"s3Uri": "s3://bucket-curso/pqrs/salida/"}},
            "timeoutDurationInHours": 24, "tags": [{"key": "curso", "value": "llm-infra"}],
        })
        batch_bedrock.enviar(bedrock, "bucket-curso", "amazon.nova-lite-v1:0", "arn:aws:iam::111122223333:role/bedrock-batch-pqrs")
        sb.add_response("get_model_invocation_job", {
            "jobArn": arn, "modelId": "amazon.nova-lite-v1:0", "roleArn": "arn:aws:iam::111122223333:role/r",
            "status": "Completed", "submitTime": "2026-10-20T00:00:00Z",
            "inputDataConfig": {"s3InputDataConfig": {"s3Uri": "s3://bucket-curso/pqrs/entrada/"}},
            "outputDataConfig": {"s3OutputDataConfig": {"s3Uri": "s3://bucket-curso/pqrs/salida/"}},
            "totalRecordCount": 120, "processedRecordCount": 120, "successRecordCount": 120, "errorRecordCount": 0,
        }, {"jobIdentifier": arn})
        assert batch_bedrock.estado(bedrock, esperar=True, intervalo_s=0)["status"] == "Completed"

    linea = b'{"recordId":"PQRS0000001","modelOutput":{"output":{"message":{"content":[{"text":"{}"}]}}}}\n'
    with Stubber(s3) as ss:
        ss.add_response("list_objects_v2", {"Contents": [
            {"Key": "pqrs/salida/abc123/lote.jsonl.out"}, {"Key": "pqrs/salida/abc123/manifest.json.out"},
        ], "IsTruncated": False}, {"Bucket": "bucket-curso", "Prefix": "pqrs/salida/"})
        ss.add_response("get_object", {"Body": StreamingBody(io.BytesIO(linea), len(linea))},
                        {"Bucket": "bucket-curso", "Key": "pqrs/salida/abc123/lote.jsonl.out"})
        manifest = b'{"totalRecordCount":120}'
        ss.add_response("get_object", {"Body": StreamingBody(io.BytesIO(manifest), len(manifest))},
                        {"Bucket": "bucket-curso", "Key": "pqrs/salida/abc123/manifest.json.out"})
        salida = batch_bedrock.descargar(s3, "bucket-curso")
    assert salida.read_bytes() == linea
