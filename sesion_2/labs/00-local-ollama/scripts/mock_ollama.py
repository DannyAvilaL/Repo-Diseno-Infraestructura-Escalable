"""Simulador didáctico de Ollama (plan de contingencia de la clase).

Emula /api/tags y /api/chat con streaming NDJSON para ejecutar las demos
cuando Ollama no está disponible. Modela las dos fases de la Unidad A:

- prefill: retardo proporcional a la longitud del prompt (TTFT)
- decode: retardo fijo por token (TPOT)
- capacidad: un número limitado de secuencias simultáneas (lote); el resto
  espera en cola, lo que hace visible la saturación en la Demo 4.

NO mide un modelo real: sus cifras son sintéticas y deben presentarse así.

Uso:
    python scripts/mock_ollama.py --port 11434 --batch 2
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

ANSWER = (
    "Respuesta simulada: para una homologación se presenta la solicitud ante la "
    "dependencia académica con el certificado de notas y los programas de las asignaturas."
).split(" ")

app = FastAPI(title="Mock Ollama")
CONFIG = {"prefill_ms_per_char": 0.5, "decode_ms_per_token": 40.0, "model": "qwen2.5:1.5b"}
SLOTS: asyncio.Semaphore


@app.get("/api/tags")
async def tags() -> dict[str, object]:
    return {"models": [{"name": CONFIG["model"]}]}


@app.post("/api/chat")
async def chat(request: Request) -> StreamingResponse:
    body = await request.json()
    prompt_chars = sum(len(m.get("content", "")) for m in body.get("messages", []))

    async def gen() -> AsyncIterator[str]:
        async with SLOTS:  # la cola aparece cuando todas las ranuras están ocupadas
            await asyncio.sleep(prompt_chars * CONFIG["prefill_ms_per_char"] / 1000)
            for i, word in enumerate(ANSWER):
                text = word if i == 0 else " " + word
                yield json.dumps({"message": {"role": "assistant", "content": text}, "done": False}) + "\n"
                await asyncio.sleep(CONFIG["decode_ms_per_token"] / 1000)
            yield json.dumps({"message": {"role": "assistant", "content": ""}, "done": True,
                              "prompt_eval_count": prompt_chars // 4, "eval_count": len(ANSWER)}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


def main() -> None:
    global SLOTS
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--batch", type=int, default=2, help="secuencias simultáneas")
    parser.add_argument("--decode-ms", type=float, default=40.0)
    args = parser.parse_args()
    CONFIG["decode_ms_per_token"] = args.decode_ms
    SLOTS = asyncio.Semaphore(args.batch)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
