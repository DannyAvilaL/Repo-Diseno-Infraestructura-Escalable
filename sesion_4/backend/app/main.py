"""LLM Gateway: capa delgada delante del servidor de inferencia (Ollama).

Responsabilidades (separación de preocupaciones, ver docs/arquitectura.md):
  1. Autenticación y validación de entrada (frontera de confianza).
  2. Control de admisión con cola acotada (backpressure / load shedding).
  3. Medición de TTFT, TPOT, latencia e2e y profundidad de cola (señales de autoscaling).
  4. Probes de salud: liveness (/healthz) y readiness (/readyz).
"""

import json
import logging
import secrets
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import __version__
from .admission import AdmissionController, QueueFullError, QueueTimeoutError
from .config import Settings, get_settings
from .metrics import Metrics, build_metrics
from .ollama_client import OllamaClient, UpstreamError
from .schemas import ChatRequest, ChatResponse, Timings, Usage

log = logging.getLogger("gateway")


def create_app(settings: Settings | None = None, transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    """Fábrica de la aplicación. `transport` permite inyectar un Ollama simulado en pruebas."""
    cfg = settings or get_settings()
    logging.basicConfig(level=cfg.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # evita ruido (y URLs) en logs

    metrics: Metrics = build_metrics()
    admission = AdmissionController(cfg.max_concurrency, cfg.max_queue, cfg.queue_timeout_s, metrics)
    client = OllamaClient(cfg.ollama_base_url, cfg.request_timeout_s, transport=transport)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await client.aclose()

    app = FastAPI(title="LLM Gateway - Sesión 4", version=__version__, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    def require_key(x_api_key: str | None = Header(default=None)) -> None:
        """Si GW_API_KEY está definida, exige el header X-API-Key (comparación en tiempo constante)."""
        if cfg.api_key is None:
            return
        expected = cfg.api_key.get_secret_value()
        if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
            raise HTTPException(status_code=401, detail="API key inválida o ausente")

    async def run_inference(req: ChatRequest) -> AsyncIterator[dict[str, Any]]:
        """Pipeline único (admisión -> inferencia -> métricas) para modo streaming y no streaming."""
        t_start = time.perf_counter()
        async with admission.slot() as waited:
            yield {"type": "admitted", "queue_wait_s": waited}
            ttft: float | None = None
            final: dict[str, Any] = {}
            t_infer = time.perf_counter()
            async for chunk in client.stream_chat(
                cfg.model,
                [m.model_dump() for m in req.messages],
                req.max_tokens,
                req.temperature,
            ):
                text = chunk.get("message", {}).get("content", "")
                if text:
                    if ttft is None:
                        ttft = time.perf_counter() - t_infer
                        metrics.ttft.observe(ttft)
                    yield {"type": "token", "text": text}
                if chunk.get("done"):
                    final = chunk
            e2e = time.perf_counter() - t_start
            out_tokens = int(final.get("eval_count", 0))
            in_tokens = int(final.get("prompt_eval_count", 0))
            tpot: float | None = None
            if ttft is not None and out_tokens > 1:
                tpot = ((time.perf_counter() - t_infer) - ttft) / (out_tokens - 1)
                metrics.tpot.observe(tpot)
            metrics.e2e.observe(e2e)
            metrics.output_tokens.inc(out_tokens)
            metrics.input_tokens.inc(in_tokens)
            metrics.requests.labels(outcome="ok").inc()
            yield {
                "type": "done",
                "usage": {"input_tokens": in_tokens, "output_tokens": out_tokens},
                "timings": {"queue_wait_s": waited, "ttft_s": ttft, "tpot_s": tpot, "e2e_s": e2e},
            }

    def http_error(exc: Exception) -> HTTPException:
        if isinstance(exc, QueueFullError):
            return HTTPException(429, "Capacidad agotada; reintente luego", headers={"Retry-After": "5"})
        if isinstance(exc, QueueTimeoutError):
            return HTTPException(503, "Tiempo de espera en cola excedido", headers={"Retry-After": "5"})
        metrics.requests.labels(outcome="upstream_error").inc()
        log.error("fallo upstream: %s", exc)
        return HTTPException(502, "Fallo del servidor de inferencia")

    @app.get("/healthz", tags=["ops"])
    async def healthz() -> dict[str, str]:
        """Liveness: el proceso responde. No depende de Ollama (evita reinicios en cascada)."""
        return {"status": "ok", "version": __version__}

    @app.get("/readyz", tags=["ops"])
    async def readyz() -> JSONResponse:
        """Readiness: Ollama responde y el modelo existe en el volumen. Controla el tráfico del Service."""
        ready = await client.is_ready(cfg.model)
        return JSONResponse({"ready": ready, "model": cfg.model}, status_code=200 if ready else 503)

    @app.get("/metrics", tags=["ops"])
    async def prometheus_metrics() -> Response:
        return Response(generate_latest(metrics.registry), media_type=CONTENT_TYPE_LATEST)

    @app.post("/v1/chat", response_model=ChatResponse, tags=["inference"], dependencies=[Depends(require_key)])
    async def chat(req: ChatRequest, request: Request) -> Any:
        agen = run_inference(req)
        try:
            await agen.__anext__()  # espera la admisión; lanza QueueFull/QueueTimeout antes de responder
        except (QueueFullError, QueueTimeoutError, UpstreamError) as exc:
            raise http_error(exc) from exc

        if req.stream:
            return StreamingResponse(_sse(agen), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

        parts: list[str] = []
        done: dict[str, Any] = {}
        try:
            async for ev in agen:
                if ev["type"] == "token":
                    parts.append(ev["text"])
                elif ev["type"] == "done":
                    done = ev
        except UpstreamError as exc:
            raise http_error(exc) from exc
        finally:
            await agen.aclose()
        return ChatResponse(
            model=cfg.model,
            content="".join(parts),
            usage=Usage(**done["usage"]),
            timings=Timings(**done["timings"]),
        )

    async def _sse(agen: AsyncIterator[dict[str, Any]]) -> AsyncIterator[str]:
        try:
            async for ev in agen:
                yield f"event: {ev['type']}\ndata: {json.dumps(ev, ensure_ascii=False)}\n\n"
        except UpstreamError as exc:
            metrics.requests.labels(outcome="upstream_error").inc()
            log.error("fallo upstream en streaming: %s", exc)
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'detail': 'upstream'})}\n\n"
        finally:
            await agen.aclose()  # libera el slot incluso si el cliente se desconecta

    return app


app = create_app()  # punto de entrada: `uvicorn app.main:app`
