"""Demo 3 · Prueba de conmutación por falla regional bajo carga.

Mantiene una carga constante contra el gateway, "apaga" la región primaria a
mitad de la prueba y la recupera después. Imprime una línea de tiempo por
ventanas y un resumen con la disponibilidad observada, la latencia y el
porcentaje de tráfico atendido por cada región.

Uso (con dos regiones simuladas y el gateway en marcha):
    python load-tests/failover_test.py --duracion 40 --falla-en 10 --recupera-en 25 \
        --admin-primaria http://127.0.0.1:9001/admin/state

Las cifras dependen del equipo y del simulador: sirven para explicar el
comportamiento (detección, conmutación, recuperación), no para dimensionar.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass

import httpx


@dataclass
class Resultado:
    t: float
    ok: bool
    e2e_ms: float
    region: str | None
    failover: bool


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=20)[18]


async def cliente(client: httpx.AsyncClient, inicio: float, fin: float, pausa_s: float, out: list[Resultado]) -> None:
    pregunta = {"messages": [{"role": "user", "content": "¿Cuál es el plazo para homologar asignaturas?"}]}
    while time.perf_counter() < fin:
        t0 = time.perf_counter()
        region, failover, ok = None, False, False
        try:
            r = await client.post("/v1/chat", json=pregunta)
            if r.status_code == 200:
                m = r.json()["metrics"]
                region, failover, ok = m.get("region"), bool(m.get("failover")), True
        except httpx.HTTPError:
            ok = False
        out.append(Resultado(t0 - inicio, ok, (time.perf_counter() - t0) * 1000, region, failover))
        await asyncio.sleep(pausa_s)


async def cambiar_estado(url: str, modo: str) -> None:
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.post(url, json={"mode": modo})
        r.raise_for_status()


async def ejecutar(args: argparse.Namespace) -> list[Resultado]:
    resultados: list[Resultado] = []
    inicio = time.perf_counter()
    fin = inicio + args.duracion
    async with httpx.AsyncClient(base_url=args.gateway, timeout=args.timeout) as client:
        tareas = [asyncio.create_task(cliente(client, inicio, fin, args.pausa, resultados)) for _ in range(args.concurrencia)]
        await asyncio.sleep(args.falla_en)
        print(f"[t={args.falla_en:>4.0f}s] Región primaria -> {args.modo_falla}")
        await cambiar_estado(args.admin_primaria, args.modo_falla)
        await asyncio.sleep(max(0.0, args.recupera_en - args.falla_en))
        print(f"[t={args.recupera_en:>4.0f}s] Región primaria -> healthy")
        await cambiar_estado(args.admin_primaria, "healthy")
        await asyncio.gather(*tareas)
    return resultados


def reportar(resultados: list[Resultado], ventana_s: float) -> dict[str, object]:
    por_ventana: dict[int, list[Resultado]] = defaultdict(list)
    for r in resultados:
        por_ventana[int(r.t // ventana_s)].append(r)
    print(f"\n{'ventana':>9} {'solic.':>6} {'error %':>8} {'p95 ms':>8}  regiones")
    for k in sorted(por_ventana):
        grupo = por_ventana[k]
        errores = sum(not r.ok for r in grupo)
        regiones = Counter(r.region for r in grupo if r.ok)
        lat = p95([r.e2e_ms for r in grupo if r.ok])
        reparto = ", ".join(f"{n}={c}" for n, c in sorted(regiones.items())) or "-"
        lat_txt = f"{lat:8.0f}" if lat is not None else f"{'-':>8}"
        print(f"{k*ventana_s:>4.0f}-{(k+1)*ventana_s:<4.0f} {len(grupo):>6} {100*errores/len(grupo):>7.1f}% {lat_txt}  {reparto}")

    total = len(resultados)
    exitos = [r for r in resultados if r.ok]
    resumen = {
        "solicitudes": total,
        "disponibilidad_observada_pct": round(100 * len(exitos) / total, 2) if total else None,
        "conmutaciones": sum(r.failover for r in exitos),
        "p95_ms": round(p95([r.e2e_ms for r in exitos]) or 0, 1),
        "por_region": dict(Counter(r.region for r in exitos)),
    }
    print("\n" + json.dumps(resumen, ensure_ascii=False, indent=2))
    return resumen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gateway", default="http://127.0.0.1:8080")
    parser.add_argument("--admin-primaria", default="http://127.0.0.1:9001/admin/state")
    parser.add_argument("--modo-falla", choices=["down", "slow", "throttle", "flaky"], default="down")
    parser.add_argument("--concurrencia", type=int, default=4)
    parser.add_argument("--pausa", type=float, default=0.2, help="Segundos entre solicitudes de cada cliente")
    parser.add_argument("--duracion", type=float, default=40)
    parser.add_argument("--falla-en", type=float, default=10)
    parser.add_argument("--recupera-en", type=float, default=25)
    parser.add_argument("--ventana", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    if not 0 < args.falla_en < args.recupera_en < args.duracion:
        parser.error("Se requiere 0 < falla-en < recupera-en < duracion")
    reportar(asyncio.run(ejecutar(args)), args.ventana)


if __name__ == "__main__":
    main()
