"""Prueba del adaptador FastAPI con un modelo simulado de ADK (sin Gemini ni red).

El modelo falso primero pide la herramienta del calendario y, al recibir su
resultado, responde con un texto. Valida el bucle completo de ADK y el
contrato de API del curso.
"""

from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi.testclient import TestClient
from google.adk.agents import Agent
from google.adk.models import BaseLlm, LlmResponse
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
from servicio_fastapi import create_app  # noqa: E402
from universidad_tools import buscar_reglamento, consultar_calendario_academico  # noqa: E402


class FakeLlm(BaseLlm):
    model: str = "modelo-simulado"

    async def generate_content_async(self, llm_request, stream: bool = False) -> AsyncGenerator[LlmResponse, None]:
        last = llm_request.contents[-1]
        responses = [p.function_response for p in last.parts if p.function_response]
        if responses:
            result = responses[0].response.get("result", responses[0].response)
            part = types.Part(text=f"Según el calendario: {result}")
        else:
            part = types.Part(
                function_call=types.FunctionCall(
                    name="consultar_calendario_academico", args={"evento": "homologaciones"}
                )
            )
        yield LlmResponse(content=types.Content(role="model", parts=[part]))


def make_client() -> TestClient:
    agent = Agent(
        name="asistente_universitario",
        model=FakeLlm(),
        instruction="Asistente de prueba",
        tools=[consultar_calendario_academico, buscar_reglamento],
    )
    return TestClient(create_app(agent))


def test_chat_completa_bucle_con_herramienta() -> None:
    client = make_client()
    r = client.post("/v1/chat", json={"messages": [{"role": "user", "content": "¿Hasta cuándo homologaciones?"}]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "15 de febrero de 2027" in body["content"]
    assert body["metrics"]["tool_calls"] == 1


def test_chat_valida_entrada() -> None:
    client = make_client()
    assert client.post("/v1/chat", json={"messages": []}).status_code == 422
    big = {"messages": [{"role": "user", "content": "x" * 5000}]}
    assert client.post("/v1/chat", json=big).status_code == 413


def test_healthz() -> None:
    assert make_client().get("/healthz").json() == {"status": "ok"}
