"""Cálculo de TTFT, TPOT y throughput (Unidad F).

TPOT = (latencia total - TTFT) / (tokens de salida - 1)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .schemas import InferenceMetrics


@dataclass
class StreamTimer:
    """Mide una generación en streaming con reloj monotónico."""

    start: float = field(default_factory=time.perf_counter)
    first_token_at: float | None = None
    chunks: int = 0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    def on_chunk(self) -> None:
        if self.first_token_at is None:
            self.first_token_at = time.perf_counter()
        self.chunks += 1

    def finish(self) -> InferenceMetrics:
        end = time.perf_counter()
        e2e_ms = (end - self.start) * 1000
        ttft_ms = None if self.first_token_at is None else (self.first_token_at - self.start) * 1000
        return compute_metrics(
            ttft_ms=ttft_ms,
            e2e_ms=e2e_ms,
            output_chunks=self.chunks,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
        )


def compute_metrics(
    *,
    ttft_ms: float | None,
    e2e_ms: float,
    output_chunks: int,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> InferenceMetrics:
    # Se prefiere el conteo de tokens del proveedor; si no existe, se usa el
    # número de fragmentos recibidos como aproximación.
    n_out = completion_tokens if completion_tokens else output_chunks
    tpot_ms = None
    tps = None
    if ttft_ms is not None and n_out > 1:
        tpot_ms = (e2e_ms - ttft_ms) / (n_out - 1)
        decode_s = (e2e_ms - ttft_ms) / 1000
        tps = (n_out - 1) / decode_s if decode_s > 0 else None
    return InferenceMetrics(
        ttft_ms=round(ttft_ms, 2) if ttft_ms is not None else None,
        e2e_ms=round(e2e_ms, 2),
        tpot_ms=round(tpot_ms, 2) if tpot_ms is not None else None,
        output_chunks=output_chunks,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        tokens_per_second=round(tps, 2) if tps is not None else None,
    )
