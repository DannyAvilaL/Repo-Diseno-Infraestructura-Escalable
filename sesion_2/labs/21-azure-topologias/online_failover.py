"""AZ-G (parte online) · Pregunta al asistente con conmutación entre dos regiones.

Uso:
    python online_failover.py "¿Cuándo inician las clases?"
    python online_failover.py "hola" --repeticiones 10          # reparto y latencia
    python online_failover.py "hola" --service-tier priority     # solo modelos/despliegues compatibles

Para demostrar la conmutación sin esperar una falla real, ponga un endpoint
inexistente como primera región (ver README, paso AZ-G.5).
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

from multiregion import AllRegionsFailed, MultiRegionChat, load_regions_from_env  # noqa: E402
from universidad_tools import INSTRUCCIONES_ASISTENTE  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pregunta")
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument("--service-tier", choices=["default", "priority"], default=None)
    args = parser.parse_args()

    load_dotenv()
    chat = MultiRegionChat(load_regions_from_env())
    messages = [
        {"role": "system", "content": INSTRUCCIONES_ASISTENTE},
        {"role": "user", "content": args.pregunta},
    ]
    regiones: Counter[str] = Counter()
    latencias: list[float] = []
    for i in range(args.repeticiones):
        try:
            ans = chat.ask(messages, service_tier=args.service_tier)
        except AllRegionsFailed as exc:
            print(f"[{i + 1}] ERROR: {exc}")
            continue
        regiones[ans.region] += 1
        latencias.append(ans.latency_ms)
        tier = f" · tier={ans.service_tier}" if ans.service_tier else ""
        print(f"[{i + 1}] región={ans.region} intentos={ans.attempts} latencia={ans.latency_ms:.0f} ms "
              f"tokens={ans.usage.get('prompt_tokens')}/{ans.usage.get('completion_tokens')}{tier}")
        if args.repeticiones == 1:
            print("\n" + ans.text)
    if args.repeticiones > 1 and latencias:
        p50 = statistics.median(latencias)
        print(f"\nReparto por región: {dict(regiones)} · p50={p50:.0f} ms · máx={max(latencias):.0f} ms")


if __name__ == "__main__":
    main()
