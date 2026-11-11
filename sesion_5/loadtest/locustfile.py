"""Alternativa con Locust (opcional): ``pip install locust`` y

    locust -f loadtest/locustfile.py --host http://localhost:8000 \
        --users 50 --spawn-rate 5 --run-time 2m --headless

Útil para rampas de carga y para observar el autoscaling en la nube.
"""

from __future__ import annotations

import os
import random

from locust import HttpUser, between, task

API_KEY = os.getenv("SLLM_LOAD_API_KEY", "dev-key-change-me")
POOL = int(os.getenv("SLLM_LOAD_UNIQUE_PROMPTS", "20"))


class ChatUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(8)
    def chat(self) -> None:
        n = random.randrange(POOL)  # noqa: S311
        self.client.post(
            "/v1/chat",
            json={"prompt": f"Explica brevemente el concepto número {n}", "temperature": 0, "max_tokens": 64},
            headers={"X-API-Key": API_KEY},
            name="/v1/chat",
        )

    @task(2)
    def job(self) -> None:
        self.client.post(
            "/v1/jobs",
            json={"prompt": "Resume la arquitectura serverless en tres puntos", "max_tokens": 128},
            headers={"X-API-Key": API_KEY},
            name="/v1/jobs",
        )
