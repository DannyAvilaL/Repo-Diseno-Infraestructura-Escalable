"""Cliente Amazon Bedrock multi-región con conmutación (API Converse).

Amazon Bedrock ofrece dos formas de usar varias regiones:

1. **Cross-Region inference (CRIS), gestionada por AWS:** se invoca un perfil
   de inferencia (prefijo ``us.``, ``eu.``, ``jp.``, ``au.`` o ``global.``) y
   Bedrock elige la región de destino. Los perfiles geográficos mantienen el
   procesamiento dentro de la geografía; el global puede usar cualquier región
   comercial. CRIS no cambia dónde se almacenan los datos (logs y
   configuraciones quedan en la región de origen).
2. **Conmutación propia entre regiones** (este módulo): útil cuando también se
   quiere sobrevivir a la falla del endpoint de la región de origen o cuando la
   política de datos no admite CRIS.

Decisiones:
- Reintentos de botocore limitados a 1 intento para conmutar de inmediato.
- Se conmuta ante throttling, 5xx, modelo no listo, timeouts y errores de
  conexión. Errores de validación, permisos o recurso inexistente se devuelven.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError

RETRYABLE_CODES = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "InternalServerException",
    "ModelNotReadyException",
    "ModelTimeoutException",
}


@dataclass
class Target:
    region: str
    model_id: str
    client: Any = None
    paused_until: float = 0.0


@dataclass
class Answer:
    text: str
    region: str
    model_id: str
    attempts: int
    latency_ms: float
    usage: dict[str, Any] = field(default_factory=dict)
    service_tier: str | None = None


class AllRegionsFailed(RuntimeError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("Todas las regiones fallaron: " + " | ".join(errors))
        self.errors = errors


def runtime_client(region: str, *, read_timeout_s: int = 60) -> Any:
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(retries={"max_attempts": 1, "mode": "standard"}, connect_timeout=3, read_timeout=read_timeout_s),
    )


def targets_from_env() -> list[Target]:
    raw = os.environ.get("AWS_TARGETS")
    if not raw:
        raise SystemExit("Defina AWS_TARGETS en .env (ver .env.example)")
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"AWS_TARGETS no es JSON válido: {exc}") from exc
    targets = [Target(region=i["region"], model_id=i["model_id"]) for i in items]
    if not targets:
        raise SystemExit("AWS_TARGETS está vacío")
    return targets


class MultiRegionBedrock:
    def __init__(self, targets: list[Target], *, clock: Callable[[], float] = time.monotonic, pause_s: float = 30.0) -> None:
        self.targets = targets
        self._clock = clock
        self._pause_s = pause_s
        for t in targets:
            if t.client is None:
                t.client = runtime_client(t.region)

    def ask(self, question: str, *, system: str, max_tokens: int = 800, service_tier: str | None = None) -> Answer:
        errors: list[str] = []
        now = self._clock()
        ordered = [t for t in self.targets if t.paused_until <= now] or list(self.targets)
        for attempt, t in enumerate(ordered, start=1):
            kwargs: dict[str, Any] = {
                "modelId": t.model_id,
                "system": [{"text": system}],
                "messages": [{"role": "user", "content": [{"text": question}]}],
                "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.2},
            }
            if service_tier:
                kwargs["serviceTier"] = {"type": service_tier}
            start = time.perf_counter()
            try:
                resp = t.client.converse(**kwargs)
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code", "")
                if code in RETRYABLE_CODES:
                    t.paused_until = self._clock() + self._pause_s
                    errors.append(f"{t.region}: {code}")
                    continue
                raise
            except (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError) as exc:
                t.paused_until = self._clock() + self._pause_s
                errors.append(f"{t.region}: {type(exc).__name__}")
                continue
            content = resp.get("output", {}).get("message", {}).get("content", [])
            return Answer(
                text="".join(c.get("text", "") for c in content),
                region=t.region,
                model_id=t.model_id,
                attempts=attempt,
                latency_ms=round((time.perf_counter() - start) * 1000, 1),
                usage=resp.get("usage", {}),
                service_tier=(resp.get("serviceTier") or {}).get("type"),
            )
        raise AllRegionsFailed(errors)
