"""Cliente Gemini multi-ubicación con conmutación (Gemini Enterprise Agent Platform).

En Google Cloud la "ubicación" del endpoint es una decisión de residencia:

- Endpoint regional (p. ej., ``us-central1``) o multirregional (``us``, ``eu``):
  el procesamiento queda dentro de esa jurisdicción.
- Endpoint ``global``: la documentación indica que la solicitud puede
  procesarse en cualquier ubicación de Google Cloud y que no ofrece
  aislamiento regional ni garantías de residencia; a cambio, mejora la
  disponibilidad ([Where your data lives and is processed]).

Este cliente intenta las ubicaciones en orden y conmuta ante 429, 5xx y
errores de conexión. Los reintentos internos del SDK se limitan a un intento
para que la conmutación sea inmediata (el SDK reintenta 5 veces por defecto).
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx
from google import genai
from google.genai import errors, types

RETRYABLE = {408, 429, 500, 502, 503, 504}


@dataclass
class Location:
    name: str
    client: Any = None
    paused_until: float = 0.0


@dataclass
class Answer:
    text: str
    location: str
    attempts: int
    latency_ms: float
    usage: dict[str, Any] = field(default_factory=dict)


class AllLocationsFailed(RuntimeError):
    def __init__(self, errs: list[str]) -> None:
        super().__init__("Todas las ubicaciones fallaron: " + " | ".join(errs))
        self.errors = errs


def build_client(project: str, location: str, *, timeout_ms: int = 30_000) -> genai.Client:
    """Cliente de la plataforma (no AI Studio): usa las credenciales de ``gcloud``."""
    return genai.Client(
        enterprise=True,
        project=project,
        location=location,
        http_options=types.HttpOptions(timeout=timeout_ms, retry_options=types.HttpRetryOptions(attempts=1)),
    )


def locations_from_env() -> tuple[str, list[str]]:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    raw = os.environ.get("GCP_LOCATIONS", '["us-central1", "us-east4"]')
    if not project:
        raise SystemExit("Defina GOOGLE_CLOUD_PROJECT en .env")
    try:
        locs = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"GCP_LOCATIONS no es JSON válido: {exc}") from exc
    if not isinstance(locs, list) or not locs:
        raise SystemExit("GCP_LOCATIONS debe ser una lista no vacía")
    return project, [str(x) for x in locs]


class MultiLocationGemini:
    def __init__(
        self,
        model: str,
        locations: list[Location],
        *,
        clock: Callable[[], float] = time.monotonic,
        pause_s: float = 30.0,
    ) -> None:
        self.model = model
        self.locations = locations
        self._clock = clock
        self._pause_s = pause_s

    def ask(self, question: str, *, system: str, max_output_tokens: int = 800, service_tier: str | None = None) -> Answer:
        errs: list[str] = []
        now = self._clock()
        ordered = [loc for loc in self.locations if loc.paused_until <= now] or list(self.locations)
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_output_tokens,
            temperature=0.2,
            service_tier=types.ServiceTier(service_tier) if service_tier else None,
        )
        for attempt, loc in enumerate(ordered, start=1):
            start = time.perf_counter()
            try:
                resp = loc.client.models.generate_content(model=self.model, contents=question, config=config)
            except errors.APIError as exc:
                if exc.code in RETRYABLE:
                    loc.paused_until = self._clock() + self._pause_s
                    errs.append(f"{loc.name}: HTTP {exc.code}")
                    continue
                raise  # 4xx: la solicitud fallaría igual en otra ubicación
            except (httpx.TransportError, TimeoutError) as exc:
                loc.paused_until = self._clock() + self._pause_s
                errs.append(f"{loc.name}: {type(exc).__name__}")
                continue
            usage = resp.usage_metadata.model_dump(exclude_none=True) if resp.usage_metadata else {}
            return Answer(
                text=resp.text or "",
                location=loc.name,
                attempts=attempt,
                latency_ms=round((time.perf_counter() - start) * 1000, 1),
                usage=usage,
            )
        raise AllLocationsFailed(errs)
