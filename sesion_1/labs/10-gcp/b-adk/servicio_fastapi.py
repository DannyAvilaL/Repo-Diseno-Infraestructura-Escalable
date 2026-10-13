"""GCP-B · Exposición del agente ADK con el contrato de API común del curso.

POST /v1/chat recibe {"messages": [...]} y responde {"model", "content", "metrics"},
igual que el backend del laboratorio local (ADR-0002). Así el frontend y la
prueba de carga de LOC-01 sirven también para el agente de Google Cloud.

Validado (13-oct-2026) con google-adk 2.12.0 y un modelo simulado en las
pruebas (tests/test_servicio.py). La invocación real a Gemini está pendiente.

Uso:
    uvicorn servicio_fastapi:app --host 127.0.0.1 --port 8100
"""

from __future__ import annotations

import time
import uuid
from typing import Literal

from fastapi import FastAPI, HTTPException
from google.adk.agents import BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field

APP_NAME = "asistente_universitario"
MAX_INPUT_CHARS = 4000


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)


class Metrics(BaseModel):
    e2e_ms: float
    tool_calls: int


class ChatResponse(BaseModel):
    model: str
    content: str
    metrics: Metrics


def create_app(agent: BaseAgent) -> FastAPI:
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    api = FastAPI(title="Asistente universitario · ADK", version="1.0.0")

    @api.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/v1/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest) -> ChatResponse:
        question = body.messages[-1]
        if question.role != "user":
            raise HTTPException(status_code=422, detail="El último mensaje debe ser del usuario")
        if sum(len(m.content) for m in body.messages) > MAX_INPUT_CHARS:
            raise HTTPException(status_code=413, detail=f"La entrada supera {MAX_INPUT_CHARS} caracteres")

        # Cada solicitud usa una sesión nueva: el historial llega en el cuerpo (API sin estado).
        user_id = "anonimo"
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=str(uuid.uuid4())
        )
        history = "\n".join(f"{m.role}: {m.content}" for m in body.messages[:-1])
        text = f"Historial:\n{history}\n\nPregunta: {question.content}" if history else question.content
        start = time.perf_counter()
        final, tool_calls = "", 0
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text=text)]),
            ):
                tool_calls += len(event.get_function_calls())
                if event.is_final_response() and event.content and event.content.parts:
                    final = "".join(p.text or "" for p in event.content.parts)
        except Exception as exc:  # errores del modelo o de autenticación
            raise HTTPException(status_code=502, detail=f"Error del agente: {exc}") from exc
        finally:
            await session_service.delete_session(app_name=APP_NAME, user_id=user_id, session_id=session.id)
        metrics = Metrics(e2e_ms=round((time.perf_counter() - start) * 1000, 2), tool_calls=tool_calls)
        return ChatResponse(model=str(getattr(agent, "model", "adk")), content=final, metrics=metrics)

    return api


def __getattr__(name: str) -> FastAPI:
    """Crea `app` solo cuando se solicita (uvicorn servicio_fastapi:app).

    Así las pruebas pueden importar `create_app` sin configurar Gemini.
    """
    if name == "app":
        from asistente_universitario.agent import root_agent

        return create_app(root_agent)
    raise AttributeError(name)
