"""Simulador de Chat Completions (Azure OpenAI / OpenAI) con llamadas a herramientas.

Permite validar SIN cuenta cloud que el código de un agente completa el bucle
modelo -> herramienta -> modelo. Comportamiento determinista:

1. Si el último mensaje no es de herramienta y la solicitud declara tools,
   responde con una llamada a la primera herramienta, con un argumento de
   ejemplo según el nombre del parámetro (evento / tema).
2. Si el último mensaje es el resultado de una herramienta, responde con un
   texto final que incluye ese resultado.

Rutas aceptadas: /chat/completions, /v1/chat/completions,
/openai/deployments/{deployment}/chat/completions y /openai/v1/chat/completions.
NO es un modelo: solo valida la integración. Uso:

    python labs/common/mock_openai_tools.py --port 8900
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI(title="Mock OpenAI con herramientas")
CALLS: list[dict[str, Any]] = []

EJEMPLOS = {"evento": "homologaciones", "tema": "homologacion"}


def _completion(model: str, message: dict[str, Any], finish: str) -> dict[str, Any]:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": message, "finish_reason": finish}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60},
    }


async def _handle(request: Request) -> dict[str, Any]:
    body = await request.json()
    CALLS.append({"path": request.url.path, "tools": [t["function"]["name"] for t in body.get("tools") or []]})
    model = body.get("model", "mock")
    messages = body.get("messages", [])
    last = messages[-1] if messages else {}
    tools = body.get("tools") or []
    if last.get("role") == "tool":
        content = f"Según la herramienta: {last.get('content')}"
        return _completion(model, {"role": "assistant", "content": content}, "stop")
    if tools:
        fn = tools[0]["function"]
        params = list((fn.get("parameters") or {}).get("properties", {}))
        args = {p: EJEMPLOS.get(p, "homologaciones") for p in params[:1]}
        call = {
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "function",
            "function": {"name": fn["name"], "arguments": json.dumps(args, ensure_ascii=False)},
        }
        return _completion(model, {"role": "assistant", "content": None, "tool_calls": [call]}, "tool_calls")
    return _completion(model, {"role": "assistant", "content": "Respuesta simulada sin herramientas."}, "stop")


def _as_sse(completion: dict[str, Any]) -> StreamingResponse:
    """Convierte una respuesta completa en eventos SSE de chat.completion.chunk."""
    choice = completion["choices"][0]
    msg = choice["message"]
    delta: dict[str, Any] = {"role": "assistant"}
    if msg.get("tool_calls"):
        delta["tool_calls"] = [{"index": i, **tc} for i, tc in enumerate(msg["tool_calls"])]
    else:
        delta["content"] = msg.get("content") or ""
    base = {k: completion[k] for k in ("id", "created", "model")} | {"object": "chat.completion.chunk"}
    chunks = [
        base | {"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
        base | {"choices": [{"index": 0, "delta": {}, "finish_reason": choice["finish_reason"]}]},
        base | {"choices": [], "usage": completion["usage"]},
    ]
    body = "".join(f"data: {json.dumps(c, ensure_ascii=False)}\n\n" for c in chunks) + "data: [DONE]\n\n"
    return StreamingResponse(iter([body]), media_type="text/event-stream")


@app.post("/chat/completions")
@app.post("/v1/chat/completions")
@app.post("/openai/v1/chat/completions")
@app.post("/openai/deployments/{deployment}/chat/completions")
async def chat(request: Request) -> Any:
    body = await request.json()
    completion = await _handle(request)
    return _as_sse(completion) if body.get("stream") else completion


@app.get("/calls")
async def calls() -> list[dict[str, Any]]:
    return CALLS


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8900)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
