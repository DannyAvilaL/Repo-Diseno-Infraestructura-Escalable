"""Fixtures: un Ollama simulado (httpx.MockTransport) para pruebas deterministas, sin GPU ni red."""

import asyncio
import json
from typing import Callable

import httpx
import pytest

from app.config import Settings
from app.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def ndjson(tokens: list[str], eval_count: int | None = None) -> bytes:
    lines = [json.dumps({"message": {"role": "assistant", "content": t}, "done": False}) for t in tokens]
    lines.append(
        json.dumps({"message": {"role": "assistant", "content": ""}, "done": True,
                    "eval_count": eval_count if eval_count is not None else len(tokens),
                    "prompt_eval_count": 7})
    )
    return ("\n".join(lines) + "\n").encode()


def make_ollama(delay: float = 0.0, tokens: list[str] | None = None, fail: bool = False,
                models: list[str] | None = None) -> Callable[[httpx.Request], httpx.Response]:
    toks = tokens or ["Hola", ", ", "mundo"]

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": m} for m in (models or ["test-model"])]})
        if request.url.path == "/api/chat":
            if fail:
                return httpx.Response(500, text="boom")
            await asyncio.sleep(delay)
            return httpx.Response(200, content=ndjson(toks))
        return httpx.Response(404)

    return handler


def build(handler, **overrides) -> "tuple":
    cfg = Settings(model="test-model", cors_origins=["http://localhost:5173"], **overrides)
    app = create_app(cfg, transport=httpx.MockTransport(handler))
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gw")
    return app, client


BODY = {"messages": [{"role": "user", "content": "hola"}]}
