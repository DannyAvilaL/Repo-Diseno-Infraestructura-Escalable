"""Prueba de carga asíncrona (stdlib + httpx) para medir latencia, throughput y rechazos.

Ejemplos:
  python loadtest/loadtest.py --url http://localhost:8000 --concurrency 8 --requests 40
  python loadtest/loadtest.py --concurrency 1,2,4,8,16 --requests 32   # barrido de concurrencia

Reporta p50/p95/p99 de latencia e2e, TTFT, TPOT, tokens/s agregados y conteo por código HTTP.
Los resultados dependen del hardware: NO se incluyen valores de referencia en el repositorio.
"""

import argparse
import asyncio
import json
import statistics
import time
from collections import Counter
from pathlib import Path

import httpx

PROMPT = "Explica en tres frases qué es un balanceador de carga L7."


def pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


async def one(client: httpx.AsyncClient, url: str, headers: dict, max_tokens: int) -> dict:
    t0 = time.perf_counter()
    try:
        r = await client.post(
            f"{url}/v1/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": PROMPT}], "max_tokens": max_tokens},
        )
    except httpx.HTTPError as exc:
        return {"code": f"ERR:{exc.__class__.__name__}", "wall": time.perf_counter() - t0}
    out = {"code": r.status_code, "wall": time.perf_counter() - t0}
    if r.status_code == 200:
        d = r.json()
        out.update(tokens=d["usage"]["output_tokens"], **d["timings"])
    return out


async def run_level(url: str, concurrency: int, total: int, headers: dict, max_tokens: int) -> dict:
    sem = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_connections=concurrency + 4)
    async with httpx.AsyncClient(timeout=300, limits=limits) as client:

        async def guarded() -> dict:
            async with sem:
                return await one(client, url, headers, max_tokens)

        t0 = time.perf_counter()
        results = await asyncio.gather(*[guarded() for _ in range(total)])
        elapsed = time.perf_counter() - t0

    ok = [r for r in results if r["code"] == 200]
    tokens = sum(r.get("tokens", 0) for r in ok)
    col = lambda k: [r[k] for r in ok if r.get(k) is not None]  # noqa: E731
    return {
        "concurrency": concurrency,
        "requests": total,
        "elapsed_s": round(elapsed, 2),
        "codes": dict(Counter(str(r["code"]) for r in results)),
        "rps": round(len(ok) / elapsed, 3),
        "tokens_per_s": round(tokens / elapsed, 2),
        "e2e_p50": pct(col("e2e_s"), 0.50), "e2e_p95": pct(col("e2e_s"), 0.95), "e2e_p99": pct(col("e2e_s"), 0.99),
        "ttft_p50": pct(col("ttft_s"), 0.50), "ttft_p95": pct(col("ttft_s"), 0.95),
        "tpot_mean": statistics.fmean(col("tpot_s")) if col("tpot_s") else None,
        "queue_wait_p95": pct(col("queue_wait_s"), 0.95),
    }


def fmt(v: object) -> str:
    return "-" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--concurrency", default="4", help="entero o lista separada por comas")
    ap.add_argument("--requests", type=int, default=20, help="solicitudes por nivel")
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--out", default=None, help="archivo JSON de salida (por defecto loadtest/results/<ts>.json)")
    a = ap.parse_args()

    headers = {"X-API-Key": a.api_key} if a.api_key else {}
    levels = [int(x) for x in a.concurrency.split(",")]
    rows = []
    for c in levels:
        print(f"-> concurrencia={c} ...", flush=True)
        rows.append(await run_level(a.url, c, a.requests, headers, a.max_tokens))

    cols = ["concurrency", "requests", "codes", "rps", "tokens_per_s", "ttft_p50", "ttft_p95",
            "tpot_mean", "e2e_p50", "e2e_p95", "e2e_p99", "queue_wait_p95"]
    print("\n" + " | ".join(cols))
    for r in rows:
        print(" | ".join(fmt(r[c]) for c in cols))

    out = Path(a.out or f"loadtest/results/{time.strftime('%Y%m%d-%H%M%S')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"url": a.url, "results": rows}, indent=2))
    print(f"\nResultados guardados en {out}")


if __name__ == "__main__":
    asyncio.run(main())
