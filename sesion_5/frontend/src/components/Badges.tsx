import type { ChatResponse } from "../api";

export function Badges({ r }: { r: ChatResponse }) {
  return (
    <div className="badges" aria-label="Metadatos de la respuesta">
      <span className={`badge ${r.cold_start ? "warn" : "ok"}`}>{r.cold_start ? "COLD START" : "warm"}</span>
      <span className={`badge ${r.cache_hit ? "ok" : ""}`}>{r.cache_hit ? "cache HIT" : r.coalesced ? "coalesced" : "cache miss"}</span>
      <span className="badge">total {r.timings.total_ms.toFixed(0)} ms</span>
      {r.timings.ttft_ms != null && <span className="badge">TTFT {r.timings.ttft_ms.toFixed(0)} ms</span>}
      {r.timings.load_ms != null && <span className="badge warn">carga modelo {r.timings.load_ms.toFixed(0)} ms</span>}
      <span className="badge">espera {r.timings.queue_wait_ms.toFixed(0)} ms</span>
      <span className="badge">{r.usage.prompt_tokens}→{r.usage.completion_tokens} tok</span>
      {r.flags.map((f) => (
        <span key={f} className="badge danger">{f}</span>
      ))}
    </div>
  );
}
