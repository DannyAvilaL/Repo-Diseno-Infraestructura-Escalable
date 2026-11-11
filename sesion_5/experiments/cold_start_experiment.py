"""Experimentos reproducibles de la sesión (proveedor ``mock`` => latencias SIMULADAS).

E1  Cold start: inicialización perezosa vs eager (mitigación nº 1).
E2  Efecto del caché según el tamaño del pool de prompts (hit ratio).
E3  Saturación y backpressure: concurrencia > capacidad -> 429 en lugar de colas infinitas.

    python -m experiments.cold_start_experiment

Genera ``experiments/results.md``. Los números dependen de la máquina: úselos para
razonar sobre la FORMA de las curvas, no como benchmarks de un modelo real.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import httpx

from loadtest.run_loadtest import MD_HEADER, run, to_markdown

ROOT = Path(__file__).resolve().parent.parent
API_KEY = "exp-key"


def start_server(port: int, **env: str) -> subprocess.Popen[bytes]:
    full_env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
        "SLLM_API_KEYS": f"{API_KEY}:exp",
        "SLLM_LOG_LEVEL": "WARNING",
        "SLLM_RATE_LIMIT_PER_MINUTE": "100000",
        **env,
    }
    return subprocess.Popen(  # noqa: S603
        [sys.executable, "-m", "uvicorn", "serverless_llm.main:app", "--port", str(port), "--log-level", "warning"],
        env=full_env,
        cwd=ROOT,
    )


def wait_healthy(port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with contextlib.suppress(httpx.HTTPError):
            if httpx.get(f"http://127.0.0.1:{port}/healthz", timeout=0.5).status_code == 200:
                return
        time.sleep(0.1)
    raise RuntimeError("el servidor no arrancó")


async def first_requests(port: int, n: int = 5) -> list[float]:
    out: list[float] = []
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}", timeout=30) as c:
        for i in range(n):
            t0 = time.perf_counter()
            await c.post(
                "/v1/chat",
                json={"prompt": f"prueba {i}", "temperature": 0.7},
                headers={"X-API-Key": API_KEY},
            )
            out.append((time.perf_counter() - t0) * 1000)
    return out


def e1_cold_start() -> str:
    rows = ["| Estrategia | 1ª petición (ms) | 2ª (ms) | 3ª (ms) | 4ª (ms) | 5ª (ms) |", "|---|---|---|---|---|---|"]
    for label, eager in (("Lazy init (sin mitigación)", "false"), ("Eager init (precarga en arranque)", "true")):
        port = 8110 if eager == "false" else 8111
        proc = start_server(port, SLLM_EAGER_INIT=eager, SLLM_MOCK_COLD_START_S="1.5", SLLM_PROVIDER="mock")
        try:
            wait_healthy(port)
            times = asyncio.run(first_requests(port))
        finally:
            proc.terminate()
            proc.wait(timeout=10)
        rows.append(f"| {label} | " + " | ".join(f"{t:.0f}" for t in times) + " |")
    return "\n".join(rows)


def e2_cache() -> str:
    port = 8120
    rows = [MD_HEADER]
    for label, pool in (("Pool 1000 prompts (≈0 % repetición)", 1000), ("Pool 50 prompts", 50), ("Pool 5 prompts", 5)):
        proc = start_server(port, SLLM_EAGER_INIT="true", SLLM_MAX_CONCURRENCY="8", SLLM_QUEUE_WAIT_TIMEOUT_S="30")
        try:
            wait_healthy(port)
            res = asyncio.run(
                run(url=f"http://127.0.0.1:{port}", api_key=API_KEY, requests=400, concurrency=16, unique_prompts=pool)
            )
        finally:
            proc.terminate()
            proc.wait(timeout=10)
        rows.append(to_markdown(label, res))
    return "\n".join(rows)


def e3_backpressure() -> str:
    port = 8130
    rows = [MD_HEADER]
    for label, wait_s in (("Sin límite de espera (cola crece)", "60"), ("Backpressure (espera ≤ 0,3 s)", "0.3")):
        proc = start_server(
            port,
            SLLM_EAGER_INIT="true",
            SLLM_MAX_CONCURRENCY="4",
            SLLM_QUEUE_WAIT_TIMEOUT_S=wait_s,
            SLLM_CACHE_ENABLED="false",
        )
        try:
            wait_healthy(port)
            res = asyncio.run(
                run(url=f"http://127.0.0.1:{port}", api_key=API_KEY, requests=200, concurrency=40, unique_prompts=200)
            )
        finally:
            proc.terminate()
            proc.wait(timeout=10)
        rows.append(to_markdown(label, res))
    return "\n".join(rows)


def main() -> None:
    env = (
        f"- Máquina: {platform.platform()} · CPU lógicas: {os.cpu_count()} · Python {platform.python_version()}\n"
        "- Proveedor: `mock` (cold start simulado 1,5 s; TTFT 120 ms; TPOT 15 ms)\n"
    )
    out = ["# Resultados de los experimentos de la Sesión 5 (SIMULADOS)\n", env]
    out += ["\n## E1 · Cold start: lazy vs eager\n", e1_cold_start()]
    out += ["\n\n## E2 · Efecto del caché\n", e2_cache()]
    out += ["\n\n## E3 · Backpressure (40 clientes concurrentes, capacidad 4)\n", e3_backpressure(), "\n"]
    text = "\n".join(out)
    (ROOT / "experiments" / "results.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
