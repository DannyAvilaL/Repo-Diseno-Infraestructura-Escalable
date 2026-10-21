"""Prueba de carga de la Demo 4: concurrencia frente a latencia.

Envía solicitudes al endpoint /v1/chat/stream con distintos niveles de
concurrencia y mide, desde el cliente, TTFT y latencia end-to-end.

Uso:
    python load-tests/loadtest.py --url http://127.0.0.1:8000 --levels 1 2 4 8 --requests 8
    python load-tests/loadtest.py --csv resultados.csv

Interpretación: al subir la concurrencia por encima de la capacidad del
servidor, las solicitudes esperan en cola y el TTFT p95 crece de forma no
lineal (curva D-26 de la Unidad F).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import statistics
import sys
import time
from dataclasses import dataclass

import httpx

PROMPT = "¿Cuáles son los requisitos generales para solicitar una homologación de asignaturas?"


@dataclass
class Result:
    ok: bool
    ttft_ms: float | None
    e2e_ms: float
    tokens: int


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    k = (len(ordered) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


async def one_request(client: httpx.AsyncClient, url: str) -> Result:
    start = time.perf_counter()
    ttft: float | None = None
    tokens = 0
    try:
        async with client.stream(
            "POST", f"{url}/v1/chat/stream",
            json={"messages": [{"role": "user", "content": PROMPT}]},
        ) as response:
            if response.status_code != 200:
                return Result(False, None, (time.perf_counter() - start) * 1000, 0)
            event = ""
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event = line.split(":", 1)[1].strip()
                elif line.startswith("data:") and event == "token":
                    if ttft is None:
                        ttft = (time.perf_counter() - start) * 1000
                    tokens += 1
                elif event == "error":
                    return Result(False, ttft, (time.perf_counter() - start) * 1000, tokens)
    except httpx.HTTPError:
        return Result(False, ttft, (time.perf_counter() - start) * 1000, tokens)
    return Result(True, ttft, (time.perf_counter() - start) * 1000, tokens)


async def run_level(url: str, concurrency: int, total: int, timeout_s: float) -> dict[str, float]:
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=timeout_s) as client:

        async def guarded() -> Result:
            async with sem:
                return await one_request(client, url)

        wall_start = time.perf_counter()
        results = await asyncio.gather(*(guarded() for _ in range(total)))
        wall_s = time.perf_counter() - wall_start

    ok = [r for r in results if r.ok]
    ttfts = [r.ttft_ms for r in ok if r.ttft_ms is not None]
    e2es = [r.e2e_ms for r in ok]
    return {
        "concurrency": concurrency,
        "requests": total,
        "errors": total - len(ok),
        "ttft_p50_ms": round(percentile(ttfts, 0.50), 1),
        "ttft_p95_ms": round(percentile(ttfts, 0.95), 1),
        "e2e_p50_ms": round(percentile(e2es, 0.50), 1),
        "e2e_p95_ms": round(percentile(e2es, 0.95), 1),
        "req_per_s": round(len(ok) / wall_s, 3),
        "tokens_per_s": round(sum(r.tokens for r in ok) / wall_s, 1),
        "mean_tokens": round(statistics.mean([r.tokens for r in ok]), 1) if ok else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 2, 4, 8])
    parser.add_argument("--requests", type=int, default=8, help="solicitudes por nivel")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--csv", default=None, help="ruta opcional para guardar resultados")
    args = parser.parse_args()

    rows = []
    header = f"{'conc':>4} {'err':>4} {'TTFT p50':>9} {'TTFT p95':>9} {'E2E p50':>9} {'E2E p95':>9} {'req/s':>7} {'tok/s':>7}"
    print(header)
    print("-" * len(header))
    for level in args.levels:
        row = asyncio.run(run_level(args.url, level, max(args.requests, level), args.timeout))
        rows.append(row)
        print(f"{row['concurrency']:>4} {row['errors']:>4} {row['ttft_p50_ms']:>9} {row['ttft_p95_ms']:>9} "
              f"{row['e2e_p50_ms']:>9} {row['e2e_p95_ms']:>9} {row['req_per_s']:>7} {row['tokens_per_s']:>7}")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nResultados guardados en {args.csv}")
    return 0 if all(r["errors"] == 0 for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
