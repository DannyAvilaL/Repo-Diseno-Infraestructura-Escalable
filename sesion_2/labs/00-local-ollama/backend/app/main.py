"""Backend del asistente universitario (laboratorio LOC-01).

Endpoints (contrato común del curso):
- GET  /healthz          -> el proceso está vivo
- GET  /readyz           -> el proveedor y el modelo están disponibles
- POST /v1/chat          -> respuesta completa + métricas
- POST /v1/chat/stream   -> Server-Sent Events: token, metrics, error, done
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from opentelemetry.trace import Status, StatusCode

from .config import Settings, get_settings
from .logging_setup import configure_logging
from .metrics import StreamTimer
from .providers import InferenceProvider, ProviderError, TextChunk, Usage, build_provider
from .schemas import ChatRequest, ChatResponse, HealthResponse
from .telemetry import record_metrics, setup_tracing, start_inference_span

logger = logging.getLogger("assistant")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.provider = build_provider(settings)
    logger.info("inicio", extra={"provider": settings.provider, "model": settings.model})
    yield
    await app.state.provider.aclose()


app = FastAPI(title="Asistente universitario · LOC-01", version="1.0.0", lifespan=lifespan)

_settings = get_settings()
setup_tracing(app, _settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_provider(request: Request) -> InferenceProvider:
    return request.app.state.provider


def build_messages(body: ChatRequest, settings: Settings) -> list[dict[str, str]]:
    total = sum(len(m.content) for m in body.messages)
    if total > settings.max_input_chars:
        raise HTTPException(
            status_code=413,
            detail=f"La entrada supera el límite de {settings.max_input_chars} caracteres",
        )
    return [{"role": "system", "content": settings.system_prompt}] + [
        m.model_dump() for m in body.messages
    ]


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", response_model=HealthResponse)
async def readyz(
    provider: InferenceProvider = Depends(get_provider),
) -> JSONResponse:
    try:
        await provider.health()
    except ProviderError as exc:
        body = HealthResponse(
            status="degraded", provider=provider.name, model=provider.model, detail=str(exc)
        )
        return JSONResponse(status_code=503, content=body.model_dump())
    body = HealthResponse(status="ok", provider=provider.name, model=provider.model)
    return JSONResponse(content=body.model_dump())


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    provider: InferenceProvider = Depends(get_provider),
) -> ChatResponse:
    messages = build_messages(body, settings)
    request_id = str(uuid.uuid4())
    timer = StreamTimer()
    parts: list[str] = []
    input_chars = sum(len(m["content"]) for m in messages)
    span = start_inference_span(provider.name, provider.model, input_chars)
    try:
        async for event in provider.stream_chat(messages):
            if isinstance(event, TextChunk):
                timer.on_chunk()
                parts.append(event.text)
            elif isinstance(event, Usage):
                timer.prompt_tokens = event.prompt_tokens
                timer.completion_tokens = event.completion_tokens
    except ProviderError as exc:
        logger.error("error_proveedor", extra={"request_id": request_id, "error": str(exc)})
        span.set_status(Status(StatusCode.ERROR, "provider_error"))
        span.end()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    metrics = timer.finish()
    record_metrics(span, metrics)
    span.end()
    logger.info(
        "chat_completado",
        extra={"request_id": request_id, "input_chars": input_chars, **metrics.model_dump()},
    )
    return ChatResponse(model=provider.model, content="".join(parts), metrics=metrics)


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/v1/chat/stream")
async def chat_stream(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    provider: InferenceProvider = Depends(get_provider),
) -> StreamingResponse:
    messages = build_messages(body, settings)
    request_id = str(uuid.uuid4())

    async def event_source() -> AsyncIterator[str]:
        timer = StreamTimer()
        span = start_inference_span(provider.name, provider.model, sum(len(m["content"]) for m in messages))
        try:
            async for event in provider.stream_chat(messages):
                if isinstance(event, TextChunk):
                    timer.on_chunk()
                    yield _sse("token", {"text": event.text})
                elif isinstance(event, Usage):
                    timer.prompt_tokens = event.prompt_tokens
                    timer.completion_tokens = event.completion_tokens
        except ProviderError as exc:
            logger.error("error_proveedor", extra={"request_id": request_id, "error": str(exc)})
            span.set_status(Status(StatusCode.ERROR, "provider_error"))
            span.end()
            yield _sse("error", {"detail": str(exc)})
            return
        metrics = timer.finish()
        record_metrics(span, metrics)
        span.end()
        logger.info("chat_stream_completado", extra={"request_id": request_id, **metrics.model_dump()})
        yield _sse("metrics", metrics.model_dump())
        yield _sse("done", {"request_id": request_id})

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "X-Request-Id": request_id},
    )
