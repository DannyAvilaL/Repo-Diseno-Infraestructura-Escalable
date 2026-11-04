"""Herramienta de dimensionamiento compartida por los agentes de los tres laboratorios.

Modelo simplificado (SUPUESTO ACADÉMICO, no una garantía de rendimiento): cada usuario concurrente
consume un flujo de `target_tps` tokens/s; cada réplica sostiene `replica_tps` tokens/s agregados.
Los valores reales deben medirse con loadtest/loadtest.py sobre el hardware real.
"""

import math


def estimate_replicas(
    concurrent_users: int,
    target_tps_per_user: float,
    replica_tps: float,
    headroom: float = 0.3,
    high_availability: bool = True,
) -> dict:
    """Estima réplicas de inferencia necesarias.

    Args:
        concurrent_users: usuarios concurrentes (>= 1).
        target_tps_per_user: tokens/s por usuario para una experiencia fluida (> 0). Ej.: 10-20.
        replica_tps: tokens/s agregados medidos por réplica (> 0).
        headroom: margen de seguridad como fracción (0 <= h < 0.9), p. ej. 0.3 = 30 %.
        high_availability: si es True agrega una réplica N+1 para tolerar la caída de una.

    Returns:
        dict con demanda, réplicas base, réplicas totales y supuestos.
    """
    if concurrent_users < 1:
        raise ValueError("concurrent_users debe ser >= 1")
    if target_tps_per_user <= 0 or replica_tps <= 0:
        raise ValueError("target_tps_per_user y replica_tps deben ser > 0")
    if not 0 <= headroom < 0.9:
        raise ValueError("headroom debe estar en [0, 0.9)")

    demand = concurrent_users * target_tps_per_user
    base = math.ceil(demand / (replica_tps * (1 - headroom)))
    total = base + (1 if high_availability else 0)
    return {
        "demand_tokens_per_s": round(demand, 2),
        "replicas_base": base,
        "replicas_total": total,
        "assumptions": {"headroom": headroom, "n_plus_1": high_availability},
    }
