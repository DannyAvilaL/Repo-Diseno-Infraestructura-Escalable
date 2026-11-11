"""Aplicación FastAPI: gateway LLM con patrones serverless.

Ejecutar en local:  ``uvicorn serverless_llm.main:app --reload``
"""


import json
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .config import Settings, get_settings
from .jobqueue import InMemoryQueue, JobRecord, JobStore, Message, WorkerPool
from .metrics import Metrics
from .providers import ProviderError, build_provider
from .schemas import (
    ChatRequest,
    ChatResponse,
    JobAccepted,
    JobStatus,
    JobView,
)
from .security import Authenticator, TokenBucketLimiter
from .service import ChatService, InstanceState, RejectedError

log = logging.getLogger("sllm.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()
    logging.basicConfig(level=cfg.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s")

    metrics = Metrics()
    instance = InstanceState()
    provider = build_provider(cfg)
    service = ChatService(settings=cfg, provider=provider, metrics=metrics, instance=instance)
    store = JobStore()
    auth = Authenticator(cfg.parsed_api_keys())
    limiter = TokenBucketLimiter(per_minute=cfg.rate_limit_per_minute)

    def _on_terminal(job: JobRecord) -> None:
        metrics.jobs.labels(status=job.status.value.lower()).inc()

    def _on_dead_letter(msg: Message) -> None:
        job = store.get(msg.job_id)
        if job and job.status not in (JobStatus.SUCCEEDED, JobStatus.DEAD):
            job.status = JobStatus.DEAD
            job.error = job.error or "Superó el máximo de recepciones (DLQ)"
            _on_terminal(job)

    queue = InMemoryQueue(
        visibility_timeout_s=cfg.queue_visibility_timeout_s,
        max_receive_count=cfg.queue_max_receive_count,
        on_dead_letter=_on_dead_letter,
    )

    async def handle_job(msg: Message) -> ChatResponse:
        return await service.chat(msg.tenant, msg.body)

    workers = WorkerPool(
        queue=queue,
        store=store,
        handler=handle_job,
        workers=cfg.worker_count,
        backoff_s=cfg.queue_retry_backoff_s,
        on_terminal=_on_terminal,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # Mitigación de cold start nº 1: inicialización EAGER (fuera del camino de la petición).
        if cfg.eager_init:
            try:
                instance.init_seconds = await provider.startup()
                metrics.init_seconds.set(instance.init_seconds)
                log.info("init eager completado en %.2fs", instance.init_seconds)
            except ProviderError as exc:
                log.warning("init eager falló (se continuará en modo perezoso): %s", exc)
        workers.start()
        try:
            yield
        finally:
            await workers.stop()
            await provider.aclose()

    app = FastAPI(
        title="Serverless LLM Gateway",
        version="1.0.0",
        description="Sesión 5 - Patrones serverless para LLMs",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["X-API-Key", "Content-Type", "Idempotency-Key"],
        expose_headers=["X-Instance-Id", "X-Cold-Start", "Retry-After"],
    )

    # ------------------------------------------------------------------
    # Dependencias
    # ------------------------------------------------------------------
    def current_tenant(x_api_key: Annotated[str | None, Header()] = None) -> str:
        tenant = auth.tenant_for(x_api_key)
        if tenant is None:
            metrics.rejected.labels(reason="unauthorized").inc()
            raise HTTPException(status_code=401, detail="API key inválida o ausente")
        if not limiter.allow(tenant):
            metrics.rejected.labels(reason="rate_limited").inc()
            raise HTTPException(
                status_code=429,
                detail="Límite de tasa excedido",
                headers={"Retry-After": str(int(limiter.retry_after_s(tenant)) + 1)},
            )
        return tenant

    Tenant = Annotated[str, Depends(current_tenant)]

    @app.exception_handler(RejectedError)
    async def _rejected(_req: Request, exc: RejectedError) -> JSONResponse:
        headers = {"Retry-After": str(int(exc.retry_after_s or 1))} if exc.status_code == 429 else None
        return JSONResponse(
            status_code=exc.status_code, content={"error": exc.reason}, headers=headers
        )

    @app.exception_handler(ProviderError)
    async def _provider_error(_req: Request, exc: ProviderError) -> JSONResponse:
        log.error("provider_error: %s", exc)
        # No filtramos detalles internos al cliente.
        return JSONResponse(status_code=502, content={"error": "upstream_unavailable"})

    @app.middleware("http")
    async def _observe(request: Request, call_next):  # type: ignore[no-untyped-def]
        started = time.perf_counter()
        response: Response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        metrics.requests.labels(route=path, status=str(response.status_code)).inc()
        metrics.latency.labels(route=path).observe(time.perf_counter() - started)
        response.headers["X-Instance-Id"] = instance.instance_id
        return response

    # ------------------------------------------------------------------
    # Operación
    # ------------------------------------------------------------------
    @app.get("/healthz", tags=["ops"])
    async def healthz() -> dict[str, str]:
        """Liveness: el proceso responde (no depende del modelo)."""
        return {"status": "ok"}

    @app.get("/readyz", tags=["ops"])
    async def readyz() -> JSONResponse:
        """Readiness: el proveedor puede atender tráfico (clave para el autoscaler/LB)."""
        ok = await provider.ready()
        return JSONResponse(status_code=200 if ok else 503, content={"ready": ok})

    @app.get("/metrics", tags=["ops"])
    async def prometheus() -> Response:
        metrics.queue_depth.set(queue.depth())
        return Response(metrics.render(), media_type="text/plain; version=0.0.4")

    @app.get("/v1/stats", tags=["ops"])
    async def stats(_tenant: Tenant) -> dict[str, object]:
        c = service.cache.stats
        return {
            "instance_id": instance.instance_id,
            "init_seconds": round(instance.init_seconds, 3),
            "served": instance.served,
            "provider": provider.name,
            "model": provider.model,
            "cache": {
                "entries": len(service.cache),
                "hits": c.hits,
                "misses": c.misses,
                "coalesced": c.coalesced,
                "hit_ratio": round(c.hit_ratio, 3),
            },
            "queue_depth": queue.depth(),
            "dead_letters": len(queue.dead_letters),
        }

    # ------------------------------------------------------------------
    # Inferencia síncrona, streaming y asíncrona
    # ------------------------------------------------------------------
    @app.post("/v1/chat", response_model=ChatResponse, tags=["chat"])
    async def chat(body: ChatRequest, tenant: Tenant, response: Response) -> ChatResponse:
        result = await service.chat(tenant, body)
        response.headers["X-Cold-Start"] = str(result.cold_start).lower()
        return result

    @app.post("/v1/chat/stream", tags=["chat"])
    async def chat_stream(body: ChatRequest, tenant: Tenant) -> StreamingResponse:
        # Validar ANTES de abrir el stream para poder devolver 4xx reales.
        service._prepare(tenant, body)  # noqa: SLF001 - validación temprana

        async def events() -> AsyncIterator[bytes]:
            try:
                async for piece in service.stream(tenant, body):
                    yield f"data: {json.dumps({'token': piece}, ensure_ascii=False)}\n\n".encode()
                yield b"event: done\ndata: {}\n\n"
            except RejectedError as exc:
                yield f"event: error\ndata: {json.dumps({'error': exc.reason})}\n\n".encode()
            except ProviderError:
                yield b'event: error\ndata: {"error": "upstream_unavailable"}\n\n'

        return StreamingResponse(
            events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
        )

    @app.post("/v1/jobs", response_model=JobAccepted, status_code=202, tags=["jobs"])
    async def submit_job(
        body: ChatRequest,
        tenant: Tenant,
        idempotency_key: Annotated[str | None, Header()] = None,
    ) -> JobAccepted:
        service._prepare(tenant, body)  # noqa: SLF001 - rechazar temprano
        job, replay = store.create(tenant, idempotency_key)
        if not replay:
            await queue.send(Message(message_id=job.job_id, job_id=job.job_id, body=body, tenant=tenant))
        return JobAccepted(
            job_id=job.job_id,
            status=job.status,
            status_url=f"/v1/jobs/{job.job_id}",
            idempotent_replay=replay,
        )

    @app.get("/v1/jobs/{job_id}", response_model=JobView, tags=["jobs"])
    async def job_status(job_id: str, tenant: Tenant) -> JobView:
        job = store.get(job_id)
        # 404 (no 403) para no revelar la existencia de trabajos de otros tenants.
        if job is None or job.tenant != tenant:
            raise HTTPException(status_code=404, detail="Trabajo no encontrado")
        return JobView(
            job_id=job.job_id,
            status=job.status,
            attempts=job.attempts,
            result=job.result,
            error=job.error,
        )

    app.state.queue = queue
    app.state.store = store
    app.state.service = service
    app.state.instance = instance
    return app


app = create_app()
