export interface HistoryRow {
  id: number;
  mode: string;
  ms: number;
  ttft?: number;
  cache: boolean;
  cold: boolean;
  instance: string;
}

export function HistoryTable({ rows }: { rows: HistoryRow[] }) {
  if (rows.length === 0) return null;
  const sorted = rows.map((r) => r.ms).sort((a, b) => a - b);
  const p = (q: number) => sorted[Math.min(sorted.length - 1, Math.round(q * (sorted.length - 1)))];
  return (
    <section className="card">
      <h2>Historial de la sesión</h2>
      <p className="hint">
        n={rows.length} · p50 {p(0.5).toFixed(0)} ms · p95 {p(0.95).toFixed(0)} ms. Observe cómo el primer
        <em> cold start </em> y los <em>cache hits</em> distorsionan el promedio: por eso se reportan percentiles.
      </p>
      <table>
        <thead>
          <tr><th>#</th><th>Modo</th><th>Total (ms)</th><th>TTFT (ms)</th><th>Caché</th><th>Cold</th><th>Instancia</th></tr>
        </thead>
        <tbody>
          {rows.slice(0, 30).map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td><td>{r.mode}</td><td>{r.ms.toFixed(0)}</td>
              <td>{r.ttft != null ? r.ttft.toFixed(0) : "-"}</td>
              <td>{r.cache ? "sí" : "no"}</td><td>{r.cold ? "sí" : "no"}</td><td>{r.instance}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
