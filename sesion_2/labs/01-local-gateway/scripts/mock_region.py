"""Simulador de una "región" de inferencia compatible con Chat Completions.

Permite demostrar en clase, sin nube y sin GPU, lo que ocurre cuando una
región falla, se vuelve lenta o limita el tráfico (429). Cada proceso del
simulador representa una región; el gateway LOC-02 las consume igual que
consumiría Ollama o un servicio gestionado.

Modos (cambian en caliente con POST /admin/state):
- healthy:  responde con latencia de prefill + decode y capacidad limitada.
- down:     responde 503 a todo (incluido el health check).
- slow:     tarda ``slow_ms`` antes del primer byte (provoca timeout en el gateway).
- throttle: responde 429 con Retry-After (cuota agotada).
- flaky:    falla con 500 en una proporción ``error_rate`` de las solicitudes.

Cifras SINTÉTICAS: sirven para explicar la forma de las curvas, no para
dimensionar infraestructura real.

Uso:
    python scripts/mock_region.py --name region-a --port 9001
    curl -X POST 127.0.0.1:9001/admin/state -H 'Content-Type: application/json' -d '{"mode":"down"}'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

Mode = Literal["healthy", "down", "slow", "throttle", "flaky"]


class SimState(BaseModel):
    mode: Mode = "healthy"
    slow_ms: int = Field(default=20_000, ge=0, le=600_000)
    error_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    retry_after_s: int = Field(default=10, ge=0, le=3600)


class SimStateUpdate(BaseModel):
    mode: Mode | None = None
    slow_ms: int | None = Field(default=None, ge=0, le=600_000)
    error_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    retry_after_s: int | None = Field(default=None, ge=0, le=3600)


# Heurística determinista para el lote PQRS: el simulador "clasifica" con
# palabras clave para que la demo batch produzca JSON válido y medible.
_TIPO = [
    (("solicito", "quisiera saber"), "peticion"),
    (("inconforme", "esperando"), "queja"),
    (("cobraron", "no aparece"), "reclamo"),
    (("sugiero", "sería útil"), "sugerencia"),
    (("felicitar", "excelente"), "felicitacion"),
]
_AREA = [
    (("inscripción", "admisión"), "admisiones"),
    (("homologación", "certificado de notas"), "registro_academico"),
    (("matrícula", "derechos de grado"), "financiera"),
    (("libros", "bases de datos"), "biblioteca"),
    (("deportivas", "orientación"), "bienestar"),
    (("plataforma virtual", "correo institucional"), "tecnologia"),
]
_PRIORIDAD = {"reclamo": "alta", "queja": "media"}


def _match(text: str, rules: list[tuple[tuple[str, ...], str]], default: str) -> str:
    low = text.lower()
    for keys, label in rules:
        if any(k in low for k in keys):
            return label
    return default


def build_reply(region: str, messages: list[dict[str, Any]]) -> str:
    system = " ".join(m.get("content", "") for m in messages if m.get("role") == "system")
    user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    if "clasificador de pqrs" in system.lower():
        tipo = _match(user, _TIPO, "peticion")
        return json.dumps(
            {
                "tipo": tipo,
                "area": _match(user, _AREA, "registro_academico"),
                "prioridad": _PRIORIDAD.get(tipo, "baja"),
                "resumen": "Clasificación simulada por palabras clave",
            },
            ensure_ascii=False,
        )
    tema = user.split("\n")[0].strip("¿? ")[:60]
    return (
        f"[{region}] Respuesta simulada sobre «{tema}». En un despliegue real, esta "
        "respuesta la generaría el modelo de la región que atendió la solicitud."
    )


def create_app(
    name: str,
    *,
    model: str = "simulado",
    capacity: int = 4,
    max_queue: int = 16,
    prefill_ms: float = 120.0,
    prefill_ms_per_1k_chars: float = 40.0,
    tpot_ms: float = 25.0,
    seed: int | None = None,
) -> FastAPI:
    app = FastAPI(title=f"Región simulada · {name}")
    # Solo para que el panel React del laboratorio pueda cambiar el modo de falla.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    state = SimState()
    slots = asyncio.Semaphore(capacity)
    waiting = 0
    rng = random.Random(seed)

    def fault() -> JSONResponse | None:
        if state.mode == "down":
            return JSONResponse(status_code=503, content={"error": {"message": f"{name} no disponible"}})
        if state.mode == "throttle":
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(state.retry_after_s)},
                content={"error": {"message": f"{name}: cuota agotada"}},
            )
        if state.mode == "flaky" and rng.random() < state.error_rate:
            return JSONResponse(status_code=500, content={"error": {"message": f"{name}: error interno"}})
        return None

    @app.get("/v1/models")
    async def models() -> JSONResponse:
        if state.mode == "down":
            return JSONResponse(status_code=503, content={"error": {"message": f"{name} no disponible"}})
        return JSONResponse({"object": "list", "data": [{"id": model, "object": "model"}]})

    @app.get("/admin/state")
    async def get_state() -> dict[str, Any]:
        return {"region": name, **state.model_dump(), "capacity": capacity, "waiting": waiting}

    @app.post("/admin/state")
    async def set_state(update: SimStateUpdate) -> dict[str, Any]:
        for key, value in update.model_dump(exclude_none=True).items():
            setattr(state, key, value)
        return {"region": name, **state.model_dump()}

    @app.post("/v1/chat/completions", response_model=None)
    async def chat(request: Request) -> JSONResponse | StreamingResponse:
        nonlocal waiting
        error = fault()
        if error is not None:
            return error
        body = await request.json()
        messages = body.get("messages") or []
        stream = bool(body.get("stream"))
        max_tokens = int(body.get("max_tokens") or 256)
        if waiting >= max_queue:
            return JSONResponse(
                status_code=429, headers={"Retry-After": "2"},
                content={"error": {"message": f"{name}: capacidad saturada"}},
            )
        input_chars = sum(len(str(m.get("content", ""))) for m in messages)
        reply = build_reply(name, messages)
        words = reply.split(" ")[:max_tokens]
        chunks = [w + (" " if i < len(words) - 1 else "") for i, w in enumerate(words)]
        prompt_tokens = max(1, input_chars // 4)

        waiting += 1
        await slots.acquire()  # cola: la espera se convierte en TTFT
        waiting -= 1
        released = False

        def release() -> None:
            nonlocal released
            if not released:
                released = True
                slots.release()

        try:
            delay = (prefill_ms + prefill_ms_per_1k_chars * input_chars / 1000) / 1000
            if state.mode == "slow":
                delay += state.slow_ms / 1000
            await asyncio.sleep(delay)
        except BaseException:
            release()
            raise

        cid = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())
        if not stream:
            try:
                await asyncio.sleep(tpot_ms * len(chunks) / 1000)
            finally:
                release()
            return JSONResponse(
                {
                    "id": cid, "object": "chat.completion", "created": created, "model": model,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": "".join(chunks)}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": len(chunks),
                              "total_tokens": prompt_tokens + len(chunks)},
                }
            )

        async def events() -> AsyncIterator[str]:
            try:
                for i, text in enumerate(chunks):
                    if i:
                        await asyncio.sleep(tpot_ms / 1000)
                    data = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
                            "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}]}
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                usage = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model, "choices": [],
                         "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": len(chunks),
                                   "total_tokens": prompt_tokens + len(chunks)}}
                yield f"data: {json.dumps(usage)}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                release()

        return StreamingResponse(events(), media_type="text/event-stream")

    return app


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="Región simulada compatible con Chat Completions")
    parser.add_argument("--name", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--host", default="127.0.0.1", help="No use 0.0.0.0 fuera de contenedores")
    parser.add_argument("--capacity", type=int, default=4)
    parser.add_argument("--tpot-ms", type=float, default=25.0)
    parser.add_argument("--prefill-ms", type=float, default=120.0)
    args = parser.parse_args()
    app = create_app(args.name, capacity=args.capacity, tpot_ms=args.tpot_ms, prefill_ms=args.prefill_ms)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
