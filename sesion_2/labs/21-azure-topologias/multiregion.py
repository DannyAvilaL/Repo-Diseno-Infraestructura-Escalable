"""Cliente multi-región para Microsoft Foundry (Azure OpenAI v1) con failover.

Patrón: conmutación del lado del cliente entre dos recursos de Foundry en
regiones distintas. Es la variante más simple de la topología activo-pasivo;
en producción la misma lógica suele vivir en un gateway (Azure API Management
con un pool de backends y circuit breaker) para no repetirla en cada cliente.

Decisiones:
- ``max_retries=0`` en el SDK: los reintentos automáticos del SDK (dos por
  defecto) retrasarían la conmutación. Aquí se reintenta en OTRA región.
- Se conmuta ante 429, 5xx, errores de conexión y tiempos de espera. Un 4xx
  distinto de 429 indica una solicitud inválida y se devuelve sin conmutar.
- Un 429 con ``retry-after-ms`` o ``Retry-After`` deja la región en pausa ese
  tiempo (como el circuit breaker de LOC-02).
- Autenticación con Microsoft Entra ID (``DefaultAzureCredential``): sin
  claves de API en el código ni en archivos.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import openai
from openai import OpenAI

TOKEN_SCOPE = "https://ai.azure.com/.default"  # documentado para el endpoint /openai/v1


@dataclass
class Region:
    name: str
    endpoint: str
    deployment: str
    client: OpenAI | None = None
    paused_until: float = 0.0


@dataclass
class Answer:
    text: str
    region: str
    attempts: int
    latency_ms: float
    usage: dict[str, Any] = field(default_factory=dict)
    service_tier: str | None = None


class AllRegionsFailed(RuntimeError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("Todas las regiones fallaron: " + " | ".join(errors))
        self.errors = errors


def load_regions_from_env() -> list[Region]:
    """Lee ``AZ_REGIONS``: lista JSON de {name, endpoint, deployment} en orden de prioridad."""
    raw = os.environ.get("AZ_REGIONS")
    if not raw:
        raise SystemExit("Defina AZ_REGIONS en .env (ver .env.example)")
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"AZ_REGIONS no es JSON válido: {exc}") from exc
    regions = []
    for item in items:
        endpoint = str(item["endpoint"]).rstrip("/")
        if not endpoint.startswith("https://"):
            raise SystemExit(f"El endpoint de {item['name']} debe usar https")
        regions.append(Region(name=item["name"], endpoint=endpoint, deployment=item["deployment"]))
    if not regions:
        raise SystemExit("AZ_REGIONS está vacío")
    return regions


def build_client(endpoint: str, *, timeout_s: float = 30.0, token_provider: Callable[[], str] | None = None) -> OpenAI:
    """Cliente del endpoint v1 con token de Entra ID (sin claves)."""
    if token_provider is None:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        token_provider = get_bearer_token_provider(DefaultAzureCredential(), TOKEN_SCOPE)
    return OpenAI(base_url=f"{endpoint}/openai/v1/", api_key=token_provider, max_retries=0, timeout=timeout_s)


def _retry_after_s(exc: openai.APIStatusError) -> float | None:
    headers = exc.response.headers
    for name, factor in (("retry-after-ms", 0.001), ("retry-after", 1.0)):
        value = headers.get(name)
        if value:
            try:
                return float(value) * factor
            except ValueError:
                return None
    return None


class MultiRegionChat:
    def __init__(
        self,
        regions: list[Region],
        *,
        clock: Callable[[], float] = time.monotonic,
        default_pause_s: float = 30.0,
        max_pause_s: float = 300.0,
    ) -> None:
        self.regions = regions
        self._clock = clock
        self._default_pause_s = default_pause_s
        self._max_pause_s = max_pause_s
        for r in regions:
            if r.client is None:
                r.client = build_client(r.endpoint)

    def ask(self, messages: list[dict[str, str]], *, max_completion_tokens: int = 800, service_tier: str | None = None) -> Answer:
        errors: list[str] = []
        attempts = 0
        now = self._clock()
        ordered = [r for r in self.regions if r.paused_until <= now] or list(self.regions)
        for region in ordered:
            attempts += 1
            start = time.perf_counter()
            kwargs: dict[str, Any] = {"model": region.deployment, "messages": messages, "max_completion_tokens": max_completion_tokens}
            if service_tier:
                kwargs["service_tier"] = service_tier
            try:
                assert region.client is not None
                resp = region.client.chat.completions.create(**kwargs)
            except openai.RateLimitError as exc:
                pause = min(_retry_after_s(exc) or self._default_pause_s, self._max_pause_s)
                region.paused_until = self._clock() + pause
                errors.append(f"{region.name}: 429 (pausa {pause:.0f} s)")
                continue
            except openai.APIStatusError as exc:
                if exc.status_code >= 500:
                    region.paused_until = self._clock() + self._default_pause_s
                    errors.append(f"{region.name}: HTTP {exc.status_code}")
                    continue
                raise  # 4xx: la solicitud fallaría igual en otra región
            except (openai.APIConnectionError, openai.APITimeoutError) as exc:
                region.paused_until = self._clock() + self._default_pause_s
                errors.append(f"{region.name}: {type(exc).__name__}")
                continue
            choice = resp.choices[0]
            return Answer(
                text=choice.message.content or "",
                region=region.name,
                attempts=attempts,
                latency_ms=round((time.perf_counter() - start) * 1000, 1),
                usage=resp.usage.model_dump() if resp.usage else {},
                service_tier=getattr(resp, "service_tier", None),
            )
        raise AllRegionsFailed(errors)
