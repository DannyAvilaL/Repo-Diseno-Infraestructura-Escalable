"""Gateway multi-región con inferencia online y por lotes (laboratorio LOC-02).

Endpoints
---------
Contrato común del curso (Sesión 1):
- GET  /healthz            el proceso está vivo
- GET  /readyz             hay al menos una región disponible
- POST /v1/chat            respuesta completa + métricas + región
- POST /v1/chat/stream     SSE: region, token, metrics, error, done

Topología (Sesión 2):
- GET  /v1/regions                       estado de salud, circuito y tráfico por región
- POST /admin/regions/{name}/disable     retira una región de la rotación (mantenimiento)
- POST /admin/regions/{name}/enable      la reincorpora

Inferencia por lotes:
- POST /v1/batches                       cuerpo JSONL; responde 202 con el trabajo
- GET  /v1/batches                       lista de trabajos
- GET  /v1/batches/{id}                  estado y conteos
- GET  /v1/batches/{id}/output           resultados JSONL
- GET  /v1/batches/{id}/errors           solicitudes fallidas JSONL
- POST /v1/batches/{id}/cancel           cancela (conserva resultados parciales)
"""

from __future__ import annotations

import json
import logging
import secrets
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from opentelemetry.trace import Status, StatusCode

from .batch import BatchProcessor, BatchStore, BatchValidationError, InvalidJobState, JobNotFound
from .config import Settings, get_settings
from .logging_setup import configure_logging
from .metrics import StreamTimer
from .region_client import RegionError, TextChunk, Usage
from .router import NoRegionAvailable, Router
from .schemas import BatchJob, BatchList, ChatRequest, ChatResponse, ReadyResponse, RegionsResponse
from .telemetry import record_metrics, record_route, setup_tracing, start_inference_span

logger = logging.getLogger("gateway")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    router = getattr(app.state, "router", None) or Router(settings)
    processor = getattr(app.state, "batch", None) or BatchProcessor(settings, router, BatchStore(settings.batch_dir))
    app.state.router, app.state.batch = router, processor
    router.start()
    processor.start()
    logger.info("inicio", extra={"routing": settings.routing, "regions": list(router.regions)})
    yield
    await processor.stop()
    await router.stop()


app = FastAPI(title="Gateway multi-región · LOC-02", version="1.0.0", lifespan=lifespan)
_settings = get_settings()
setup_tracing(app, _settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)


def get_router(request: Request) -> Router:
    return request.app.state.router


def get_batch(request: Request) -> BatchProcessor:
    return request.app.state.batch


def require_admin(
    settings: Settings = Depends(get_settings),
    x_admin_token: str | None = Header(default=None),
) -> None:
    if settings.admin_token and not secrets.compare_digest(x_admin_token or "", settings.admin_token):
        raise HTTPException(status_code=401, detail="Token de administración inválido")


def build_messages(body: ChatRequest, settings: Settings) -> list[dict[str, str]]:
    total = sum(len(m.content) for m in body.messages)
    if total > settings.max_input_chars:
        raise HTTPException(status_code=413, detail=f"La entrada supera {settings.max_input_chars} caracteres")
    return [{"role": "system", "content": settings.system_prompt}] + [m.model_dump() for m in body.messages]


# ----------------------------------------------------------------- salud
@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", response_model=ReadyResponse)
async def readyz(router: Router = Depends(get_router)) -> JSONResponse:
    available = router.available_regions()
    if not available:
        body = ReadyResponse(
            status="degraded", routing=router.settings.routing, available_regions=[],
            detail="Ninguna región está sana; revise GET /v1/regions",
        )
        return JSONResponse(status_code=503, content=body.model_dump())
    return JSONResponse(content=ReadyResponse(status="ok", routing=router.settings.routing, available_regions=available).model_dump())


@app.get("/v1/regions", response_model=RegionsResponse)
async def regions(router: Router = Depends(get_router)) -> RegionsResponse:
    return router.status()


@app.post("/admin/regions/{name}/{action}", dependencies=[Depends(require_admin)], response_model=RegionsResponse)
async def admin_region(name: str, action: str, router: Router = Depends(get_router)) -> RegionsResponse:
    if action not in {"enable", "disable"}:
        raise HTTPException(status_code=404, detail="Acción no soportada")
    state = router.regions.get(name)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Región desconocida: {name}")
    state.disabled = action == "disable"
    logger.warning("region_admin", extra={"region": name, "action": action})
    return router.status()


# ---------------------------------------------------------------- online
def _no_region_detail(exc: NoRegionAvailable) -> str:
    return f"{exc}. Detalle: {'; '.join(exc.errors)}" if exc.errors else str(exc)


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    router: Router = Depends(get_router),
) -> ChatResponse:
    messages = build_messages(body, settings)
    request_id = str(uuid.uuid4())
    span = start_inference_span("chat", sum(len(m["content"]) for m in messages))
    router.online_inflight += 1
    timer = StreamTimer()
    try:
        try:
            state, response, attempts = await router.open_stream(
                messages, max_tokens=settings.max_output_tokens, temperature=settings.temperature
            )
        except NoRegionAvailable as exc:
            span.set_status(Status(StatusCode.ERROR, "no_region"))
            raise HTTPException(status_code=503, detail=_no_region_detail(exc)) from exc
        except RegionError as exc:
            span.set_status(Status(StatusCode.ERROR, "bad_request"))
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        record_route(span, region=state.name, model=state.client.model, attempts=attempts)
        parts: list[str] = []
        completed = failed = False
        try:
            async for event in state.client.iter_stream(response):
                if isinstance(event, TextChunk):
                    timer.on_chunk()
                    parts.append(event.text)
                elif isinstance(event, Usage):
                    timer.prompt_tokens, timer.completion_tokens = event.prompt_tokens, event.completion_tokens
            completed = True
        except RegionError as exc:
            failed = True
            router.finish(state, ok=False, error=exc)
            span.set_status(Status(StatusCode.ERROR, "mid_stream"))
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        finally:
            await response.aclose()
            if not completed and not failed:
                router.release(state)
        metrics = timer.finish().model_copy(update={"region": state.name, "attempts": attempts, "failover": attempts > 1})
        router.finish(state, ok=True, ttft_ms=metrics.ttft_ms)
        record_metrics(span, metrics)
        logger.info("chat_completado", extra={"request_id": request_id, **metrics.model_dump()})
        return ChatResponse(model=state.client.model, content="".join(parts), metrics=metrics)
    finally:
        router.online_inflight -= 1
        span.end()


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/v1/chat/stream")
async def chat_stream(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    router: Router = Depends(get_router),
) -> StreamingResponse:
    messages = build_messages(body, settings)
    request_id = str(uuid.uuid4())

    async def event_source() -> AsyncIterator[str]:
        span = start_inference_span("chat", sum(len(m["content"]) for m in messages))
        router.online_inflight += 1
        timer = StreamTimer()
        try:
            try:
                state, response, attempts = await router.open_stream(
                    messages, max_tokens=settings.max_output_tokens, temperature=settings.temperature
                )
            except NoRegionAvailable as exc:
                span.set_status(Status(StatusCode.ERROR, "no_region"))
                yield _sse("error", {"detail": _no_region_detail(exc)})
                return
            except RegionError as exc:
                span.set_status(Status(StatusCode.ERROR, "bad_request"))
                yield _sse("error", {"detail": str(exc)})
                return
            record_route(span, region=state.name, model=state.client.model, attempts=attempts)
            completed = failed = False
            try:
                yield _sse("region", {"name": state.name, "attempts": attempts, "failover": attempts > 1})
                async for event in state.client.iter_stream(response):
                    if isinstance(event, TextChunk):
                        timer.on_chunk()
                        yield _sse("token", {"text": event.text})
                    elif isinstance(event, Usage):
                        timer.prompt_tokens, timer.completion_tokens = event.prompt_tokens, event.completion_tokens
                completed = True
            except RegionError as exc:
                # Ya se enviaron tokens: no se conmuta para no duplicar texto.
                failed = True
                router.finish(state, ok=False, error=exc)
                span.set_status(Status(StatusCode.ERROR, "mid_stream"))
                yield _sse("error", {"detail": f"{exc}. La respuesta se interrumpió; reintente la pregunta."})
                return
            finally:
                await response.aclose()
                if not completed and not failed:
                    # El cliente cerró la conexión: se libera la región sin culparla.
                    router.release(state)
            metrics = timer.finish().model_copy(update={"region": state.name, "attempts": attempts, "failover": attempts > 1})
            router.finish(state, ok=True, ttft_ms=metrics.ttft_ms)
            record_metrics(span, metrics)
            logger.info("chat_stream_completado", extra={"request_id": request_id, **metrics.model_dump()})
            yield _sse("metrics", metrics.model_dump())
            yield _sse("done", {"request_id": request_id})
        finally:
            router.online_inflight -= 1
            span.end()

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Request-Id": request_id},
    )


# ----------------------------------------------------------------- batch
@app.post("/v1/batches", status_code=202, response_model=BatchJob)
async def create_batch(
    request: Request,
    description: str | None = Query(default=None, max_length=200),
    settings: Settings = Depends(get_settings),
    processor: BatchProcessor = Depends(get_batch),
) -> BatchJob:
    raw = await request.body()
    if len(raw) > settings.batch_max_bytes:
        raise HTTPException(status_code=413, detail=f"El archivo supera {settings.batch_max_bytes} bytes")
    try:
        return processor.submit(raw, description)
    except BatchValidationError as exc:
        raise HTTPException(status_code=400, detail={"message": "Archivo de lote inválido", "errors": exc.errors}) from exc


@app.get("/v1/batches", response_model=BatchList)
async def list_batches(processor: BatchProcessor = Depends(get_batch)) -> BatchList:
    return BatchList(data=processor.store.list())


def _load(processor: BatchProcessor, job_id: str) -> BatchJob:
    try:
        return processor.store.load(job_id)
    except JobNotFound as exc:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado") from exc


@app.get("/v1/batches/{job_id}", response_model=BatchJob)
async def get_batch_job(job_id: str, processor: BatchProcessor = Depends(get_batch)) -> BatchJob:
    return _load(processor, job_id)


@app.get("/v1/batches/{job_id}/{kind}")
async def batch_file(job_id: str, kind: str, processor: BatchProcessor = Depends(get_batch)) -> FileResponse:
    if kind not in {"output", "errors"}:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    _load(processor, job_id)
    path = processor.store.output_path(job_id) if kind == "output" else processor.store.error_path(job_id)
    if not path.exists():
        path.touch()  # un trabajo sin resultados devuelve un archivo vacío, como los servicios gestionados
    return FileResponse(path, media_type="application/jsonl", filename=f"{job_id}.{kind}.jsonl")


@app.post("/v1/batches/{job_id}/cancel", response_model=BatchJob)
async def cancel_batch(job_id: str, processor: BatchProcessor = Depends(get_batch)) -> BatchJob:
    _load(processor, job_id)
    try:
        return processor.cancel(job_id)
    except InvalidJobState as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.middleware("http")
async def access_log(request: Request, call_next):  # type: ignore[no-untyped-def]
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path not in {"/healthz", "/v1/regions"}:
        logger.info(
            "http",
            extra={"method": request.method, "path": request.url.path, "status": response.status_code,
                   "ms": round((time.perf_counter() - start) * 1000, 1)},
        )
    return response
