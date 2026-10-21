"""GCP-D (parte online) · Asistente con conmutación entre ubicaciones de Gemini.

Uso:
    python online_failover.py "¿Cuándo inician las clases?"
    python online_failover.py "hola" --repeticiones 10
    python online_failover.py "hola" --service-tier flex      # verifique soporte del modelo

Para demostrar la conmutación, ponga primero una ubicación inválida en
GCP_LOCATIONS (README, paso GCP-D.4).
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

from multiregion_gcp import AllLocationsFailed, Location, MultiLocationGemini, build_client, locations_from_env  # noqa: E402
from universidad_tools import INSTRUCCIONES_ASISTENTE  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pregunta")
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument("--service-tier", choices=["standard", "flex", "priority"], default=None)
    args = parser.parse_args()

    load_dotenv()
    model = os.environ.get("GEMINI_MODEL")
    if not model:
        raise SystemExit("Defina GEMINI_MODEL en .env con un modelo vigente de Model Garden")
    project, names = locations_from_env()
    chat = MultiLocationGemini(model, [Location(n, build_client(project, n)) for n in names])

    reparto: Counter[str] = Counter()
    latencias: list[float] = []
    for i in range(args.repeticiones):
        try:
            ans = chat.ask(args.pregunta, system=INSTRUCCIONES_ASISTENTE, service_tier=args.service_tier)
        except AllLocationsFailed as exc:
            print(f"[{i + 1}] ERROR: {exc}")
            continue
        reparto[ans.location] += 1
        latencias.append(ans.latency_ms)
        print(f"[{i + 1}] ubicación={ans.location} intentos={ans.attempts} latencia={ans.latency_ms:.0f} ms "
              f"tokens={ans.usage.get('prompt_token_count')}/{ans.usage.get('candidates_token_count')}")
        if args.repeticiones == 1:
            print("\n" + ans.text)
    if args.repeticiones > 1 and latencias:
        print(f"\nReparto: {dict(reparto)} · p50={statistics.median(latencias):.0f} ms · máx={max(latencias):.0f} ms")


if __name__ == "__main__":
    main()
