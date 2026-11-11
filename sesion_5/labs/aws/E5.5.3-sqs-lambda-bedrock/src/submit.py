"""API HTTP: POST /jobs encola (202) y GET /jobs/{id} consulta estado."""
from __future__ import annotations

import json
import os
import uuid
from typing import Any

import boto3

_sqs = boto3.client("sqs")
_table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
QUEUE_URL = os.environ["QUEUE_URL"]


def _resp(code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {"statusCode": code, "headers": {"content-type": "application/json"}, "body": json.dumps(body)}


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    method = event["requestContext"]["http"]["method"]
    if method == "GET":
        job_id = event["pathParameters"]["job_id"]
        item = _table.get_item(Key={"job_id": job_id}).get("Item")
        return _resp(200, {k: str(v) for k, v in item.items()}) if item else _resp(404, {"error": "not_found"})
    try:
        payload = json.loads(event.get("body") or "{}")
        prompt = payload["prompt"]
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000:
            raise ValueError("prompt invalido")
    except (KeyError, ValueError, json.JSONDecodeError):
        return _resp(400, {"error": "bad_request"})
    job_id = str(uuid.uuid4())
    _sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps({"job_id": job_id, "prompt": prompt}))
    return _resp(202, {"job_id": job_id, "status": "PENDING"})
