"""Cloud Run function (CloudEvent) disparada por Pub/Sub; llama a Gemini via google-genai (Vertex)."""
from __future__ import annotations

import base64
import json
import logging
import os

import functions_framework
from cloudevents.http import CloudEvent
from google import genai

logging.basicConfig(level=logging.INFO)
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ["GOOGLE_CLOUD_LOCATION"],
        )
    return _client


@functions_framework.cloud_event
def procesar(event: CloudEvent) -> None:
    """Lanza excepcion ante fallo transitorio => Pub/Sub reintenta y, con dead-letter topic, termina en DLQ."""
    raw = base64.b64decode(event.data["message"]["data"]).decode("utf-8")
    msg = json.loads(raw)
    prompt = str(msg["prompt"])[:4000]
    resp = _get_client().models.generate_content(model=os.environ["GEMINI_MODEL"], contents=prompt)
    logging.info("job=%s tokens=%s", msg.get("job_id"), getattr(resp.usage_metadata, "total_token_count", None))
    # En produccion: persistir resultado (Firestore/Cloud SQL) con clave idempotente job_id.
