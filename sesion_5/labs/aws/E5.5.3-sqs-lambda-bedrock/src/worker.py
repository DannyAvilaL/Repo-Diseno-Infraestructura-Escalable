"""Worker SQS -> Bedrock Converse con idempotencia y partial batch response."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializacion FUERA del handler: se ejecuta en la fase INIT (y queda en el snapshot de SnapStart).
_bedrock = boto3.client("bedrock-runtime", config=Config(retries={"max_attempts": 2, "mode": "standard"}, read_timeout=50))
_table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
MODEL_ID = os.environ["MODEL_ID"]
MAX_PROMPT_CHARS = int(os.environ.get("MAX_PROMPT_CHARS", "4000"))


def _process(body: dict[str, Any]) -> None:
    job_id = body["job_id"]
    prompt = str(body["prompt"])[:MAX_PROMPT_CHARS]
    # Idempotencia: SQS es at-least-once. Escritura condicional evita doble procesamiento.
    try:
        _table.put_item(
            Item={"job_id": job_id, "status": "RUNNING", "expires_at": int(time.time()) + 86400},
            ConditionExpression="attribute_not_exists(job_id) OR #s = :failed",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":failed": "FAILED"},
        )
    except _table.meta.client.exceptions.ConditionalCheckFailedException:
        logger.info("job %s ya procesado/en curso: se omite", job_id)
        return
    t0 = time.perf_counter()
    try:
        resp = _bedrock.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0},
        )
        text = resp["output"]["message"]["content"][0]["text"]
        _table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #s=:s, result=:r, usage=:u, latency_ms=:l",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": "SUCCEEDED", ":r": text,
                ":u": json.dumps(resp.get("usage", {})), ":l": int((time.perf_counter() - t0) * 1000),
            },
        )
    except Exception:
        _table.update_item(Key={"job_id": job_id}, UpdateExpression="SET #s=:s",
                           ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":s": "FAILED"})
        raise


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    for record in event["Records"]:
        try:
            _process(json.loads(record["body"]))
        except Exception:  # noqa: BLE001 - se reporta item fallido; SQS reintenta y luego envia a DLQ
            logger.exception("fallo procesando messageId=%s", record["messageId"])
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
