"""Prueba de carga asíncrona (sin dependencias extra) para el gateway.

Mide lo que importa en la sesión: latencia p50/p95/p99, throughput, tasa de
errores/429, proporción de aciertos de caché y arranques en frío.

Uso:
    python -m loadtest.run_loadtest --url http://localhost:8000 --api-key dev-key-change-me \
        --requests 200 --concurrency 20 --unique-prompts 20

NOTA DIDÁCTICA: con el proveedor ``mock`` las latencias son simuladas. Con
``ollama`` o con un servicio cloud reales, los números pasan a ser medidos, pero
dependen del hardware, el modelo y la región: reporte siempre el entorno.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import asdict, dataclass, field

import httpx


@dataclass
class Result:
    requests: int
    concurrency: int
    duration_s: float
    throughput_rps: float
    status_counts: dict[str, int]
    latency_ms: dict[str, float]
    cache_hit_ratio: float
    cold_starts: int
    error_rate: float
    notes: list[str] = field(default_factory=list)


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(len(sorted_values) - 1, max(0, round(q / 100 * (len(sorted_values) - 1))))
    return sorted_values[idx]


async def run(
    *,
    url: str,
    api_key: str,
    requests: int,
    concurrency: int,
    unique_prompts: int,
    temperature: float = 0.0,
    max_tokens: int = 64,
    timeout_s: float = 60.0,
) -> Result:
    sem = asyncio.Semaphore(concurrency)
    latencies: list[float] = []
    statuses: dict[str, int] = {}
    cache_hits = 0
    cold = 0
    ok_bodies = 0

    async with httpx.AsyncClient(base_url=url, timeout=timeout_s) as client:

        async def one(i: int) -> None:
            nonlocal cache_hits, cold, ok_bodies
            body = {
                "prompt": f"Explica brevemente el concepto número {i % unique_prompts}",
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            async with sem:
                started = time.perf_counter()
                try:
                    resp = await client.post("/v1/chat", json=body, headers={"X-API-Key": api_key})
                    code = str(resp.status_code)
                except httpx.HTTPError as exc:
                    code = type(exc).__name__
                    resp = None
                elapsed = (time.perf_counter() - started) * 1000
            statuses[code] = statuses.get(code, 0) + 1
            latencies.append(elapsed)
            if resp is not None and resp.status_code == 200:
                data = resp.json()
                ok_bodies += 1
                cache_hits += bool(data.get("cache_hit") or data.get("coalesced"))
                cold += bool(data.get("cold_start"))

        started_all = time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(requests)))
        duration = time.perf_counter() - started_all

    latencies.sort()
    errors = sum(v for k, v in statuses.items() if k != "200")
    return Result(
        requests=requests,
        concurrency=concurrency,
        duration_s=round(duration, 3),
        throughput_rps=round(requests / duration, 2) if duration else 0.0,
        status_counts=statuses,
        latency_ms={
            "mean": round(statistics.fmean(latencies), 1) if latencies else 0.0,
            "p50": round(percentile(latencies, 50), 1),
            "p95": round(percentile(latencies, 95), 1),
            "p99": round(percentile(latencies, 99), 1),
            "max": round(latencies[-1], 1) if latencies else 0.0,
        },
        cache_hit_ratio=round(cache_hits / ok_bodies, 3) if ok_bodies else 0.0,
        cold_starts=cold,
        error_rate=round(errors / requests, 3) if requests else 0.0,
    )


def to_markdown(label: str, r: Result) -> str:
    lat = r.latency_ms
    return (
        f"| {label} | {r.requests} | {r.concurrency} | {r.throughput_rps} | "
        f"{lat['p50']} | {lat['p95']} | {lat['p99']} | {r.cache_hit_ratio:.0%} | "
        f"{r.error_rate:.0%} | {r.status_counts} |"
    )


MD_HEADER = (
    "| Escenario | Peticiones | Concurrencia | RPS | p50 ms | p95 ms | p99 ms | Caché | Error | Códigos |\n"
    "|---|---|---|---|---|---|---|---|---|---|"
)


def _main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--api-key", default="dev-key-change-me")
    ap.add_argument("--requests", type=int, default=100)
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument("--unique-prompts", type=int, default=10, help="Tamaño del pool de prompts (controla el hit ratio)")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--json", action="store_true", help="Salida JSON en lugar de tabla")
    args = ap.parse_args()
    result = asyncio.run(
        run(
            url=args.url,
            api_key=args.api_key,
            requests=args.requests,
            concurrency=args.concurrency,
            unique_prompts=args.unique_prompts,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    )
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(MD_HEADER)
        print(to_markdown("ad-hoc", result))


if __name__ == "__main__":
    _main()
