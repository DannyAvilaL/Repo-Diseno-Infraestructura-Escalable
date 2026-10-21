"""AWS-E (parte online) · Asistente con conmutación entre regiones de Bedrock.

Uso:
    python online_failover.py "¿Cuándo inician las clases?"
    python online_failover.py "hola" --repeticiones 10
    python online_failover.py "hola" --service-tier flex     # verifique soporte del modelo
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

from multiregion_aws import AllRegionsFailed, MultiRegionBedrock, targets_from_env  # noqa: E402
from universidad_tools import INSTRUCCIONES_ASISTENTE  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pregunta")
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument("--service-tier", choices=["default", "flex", "priority"], default=None)
    args = parser.parse_args()

    load_dotenv()
    chat = MultiRegionBedrock(targets_from_env())
    reparto: Counter[str] = Counter()
    latencias: list[float] = []
    for i in range(args.repeticiones):
        try:
            ans = chat.ask(args.pregunta, system=INSTRUCCIONES_ASISTENTE, service_tier=args.service_tier)
        except AllRegionsFailed as exc:
            print(f"[{i + 1}] ERROR: {exc}")
            continue
        reparto[ans.region] += 1
        latencias.append(ans.latency_ms)
        tier = f" · tier={ans.service_tier}" if ans.service_tier else ""
        print(f"[{i + 1}] región={ans.region} modelo={ans.model_id} intentos={ans.attempts} "
              f"latencia={ans.latency_ms:.0f} ms tokens={ans.usage.get('inputTokens')}/{ans.usage.get('outputTokens')}{tier}")
        if args.repeticiones == 1:
            print("\n" + ans.text)
    if args.repeticiones > 1 and latencias:
        print(f"\nReparto: {dict(reparto)} · p50={statistics.median(latencias):.0f} ms · máx={max(latencias):.0f} ms")


if __name__ == "__main__":
    main()
