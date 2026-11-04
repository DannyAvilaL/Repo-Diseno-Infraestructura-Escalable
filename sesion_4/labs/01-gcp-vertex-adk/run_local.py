"""Ejecuta el agente ADK desde Python (sin `adk web`) usando Runner + sesión en memoria.

Uso:  python run_local.py "Tengo 100 usuarios concurrentes, 15 tok/s por usuario y una réplica da 400 tok/s"
"""

import asyncio
import sys

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv("capacity_agent/.env")
from capacity_agent.agent import root_agent  # noqa: E402  (después de cargar el entorno)

APP, USER = "capacity_app", "estudiante"


async def main(question: str) -> None:
    sessions = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP, session_service=sessions)
    session = await sessions.create_session(app_name=APP, user_id=USER)
    message = types.Content(role="user", parts=[types.Part(text=question)])
    async for event in runner.run_async(user_id=USER, session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    asyncio.run(main(" ".join(sys.argv[1:])))
