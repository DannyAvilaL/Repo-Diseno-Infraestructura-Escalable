import { useCallback, useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------- tipos
type Metrics = {
  ttft_ms: number | null;
  e2e_ms: number;
  tpot_ms: number | null;
  completion_tokens: number | null;
  tokens_per_second: number | null;
  region: string | null;
  attempts: number;
  failover: boolean;
};

type Region = {
  name: string;
  priority: number;
  weight: number;
  healthy: boolean;
  health_detail: string | null;
  circuit: "closed" | "open" | "half_open";
  circuit_open_remaining_s: number;
  disabled: boolean;
  inflight: number;
  requests: number;
  successes: number;
  failures: number;
  last_error: string | null;
  ewma_ttft_ms: number | null;
  sim_admin_url: string | null;
};

type Job = {
  id: string;
  status: string;
  description: string | null;
  created_at: number;
  request_counts: { total: number; completed: number; failed: number };
  regions_used: Record<string, number>;
  errors: string[];
};

type Tab = "online" | "regiones" | "lotes";
const MODES = ["healthy", "down", "slow", "throttle", "flaky"] as const;
const MODE_LABEL: Record<(typeof MODES)[number], string> = {
  healthy: "Sana",
  down: "Caída",
  slow: "Lenta",
  throttle: "429",
  flaky: "Intermitente",
};
const TERMINAL = new Set(["completed", "failed", "expired", "cancelled"]);

// --------------------------------------------------------------- utilidades
function fmt(v: number | null | undefined, unit = "ms"): string {
  return v === null || v === undefined ? "–" : `${v.toFixed(0)} ${unit}`;
}

function usePolling<T>(url: string, intervalMs: number): [T | null, () => void] {
  const [data, setData] = useState<T | null>(null);
  const load = useCallback(async () => {
    try {
      const r = await fetch(url);
      if (r.ok) setData((await r.json()) as T);
    } catch {
      /* el panel sigue mostrando el último estado conocido */
    }
  }, [url]);
  useEffect(() => {
    load();
    const id = window.setInterval(load, intervalMs);
    return () => window.clearInterval(id);
  }, [load, intervalMs]);
  return [data, load];
}

// Lote de ejemplo generado en el navegador (mismo formato que scripts/generar_lote.py).
function sampleBatch(n: number): string {
  const system =
    "Eres un clasificador de PQRS de una universidad. Responde SOLO con un objeto JSON con las claves tipo, area, prioridad y resumen.";
  const textos = [
    "Solicito información sobre la homologación de asignaturas.",
    "Me cobraron dos veces por la matrícula del periodo.",
    "Sugiero mejorar el proceso de préstamo de libros.",
    "Llevo dos semanas esperando respuesta sobre el correo institucional.",
    "Quiero felicitar al equipo que me ayudó con la entrevista de admisión.",
  ];
  return Array.from({ length: n }, (_, i) =>
    JSON.stringify({
      custom_id: `WEB${String(i + 1).padStart(5, "0")}`,
      method: "POST",
      url: "/v1/chat/completions",
      body: {
        model: "simulado",
        messages: [
          { role: "system", content: system },
          { role: "user", content: textos[i % textos.length] },
        ],
      },
    }),
  ).join("\n");
}

// ------------------------------------------------------------------ online
function OnlineTab() {
  const [input, setInput] = useState("¿Cuál es el plazo para homologar asignaturas?");
  const [answer, setAnswer] = useState("");
  const [route, setRoute] = useState<{ name: string; attempts: number; failover: boolean } | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setAnswer("");
    setRoute(null);
    setMetrics(null);
    setError(null);
    try {
      const r = await fetch("/v1/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [{ role: "user", content: input }] }),
      });
      if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buffer.indexOf("\n\n")) >= 0) {
          const block = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const event = /^event: (.*)$/m.exec(block)?.[1];
          const data = JSON.parse(/^data: (.*)$/m.exec(block)?.[1] ?? "{}");
          if (event === "region") setRoute(data);
          else if (event === "token") setAnswer((a) => a + data.text);
          else if (event === "metrics") setMetrics(data);
          else if (event === "error") setError(data.detail);
        }
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <form onSubmit={send}>
        <input value={input} onChange={(e) => setInput(e.target.value)} maxLength={4000} aria-label="Pregunta" />
        <button disabled={busy || !input.trim()}>{busy ? "…" : "Enviar"}</button>
      </form>
      {route && (
        <p className="route">
          Atendió <strong>{route.name}</strong>
          {route.failover && <span className="badge warn">conmutación tras {route.attempts - 1} falla(s)</span>}
        </p>
      )}
      {answer && <article>{answer}</article>}
      {error && <p className="error">{error}</p>}
      {metrics && (
        <div className="metrics">
          <span>TTFT {fmt(metrics.ttft_ms)}</span>
          <span>TPOT {fmt(metrics.tpot_ms)}</span>
          <span>Total {fmt(metrics.e2e_ms)}</span>
          <span>{metrics.completion_tokens ?? "–"} tokens</span>
          <span>{fmt(metrics.tokens_per_second, "tok/s")}</span>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------- regiones
function RegionsTab() {
  const [status, reload] = usePolling<{ routing: string; online_inflight: number; regions: Region[] }>(
    "/v1/regions",
    1500,
  );
  const [token, setToken] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  async function simulate(r: Region, mode: (typeof MODES)[number]) {
    if (!r.sim_admin_url) return;
    try {
      const res = await fetch(r.sim_admin_url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, slow_ms: 20000, retry_after_s: 20 }),
      });
      setMsg(res.ok ? `${r.name}: modo ${MODE_LABEL[mode]}` : `No se pudo cambiar ${r.name} (HTTP ${res.status})`);
    } catch {
      setMsg(`No se pudo contactar el simulador de ${r.name}`);
    }
  }

  async function toggle(r: Region) {
    const action = r.disabled ? "enable" : "disable";
    const res = await fetch(`/admin/regions/${r.name}/${action}`, {
      method: "POST",
      headers: token ? { "X-Admin-Token": token } : {},
    });
    setMsg(res.ok ? `${r.name}: ${action === "disable" ? "retirada de la rotación" : "reincorporada"}` : `HTTP ${res.status}`);
    reload();
  }

  if (!status) return <p className="muted">Cargando estado de las regiones…</p>;
  return (
    <section>
      <p className="muted">
        Enrutamiento <strong>{status.routing === "priority" ? "activo-pasivo (prioridad)" : "activo-activo"}</strong> ·
        solicitudes online en curso: {status.online_inflight}
      </p>
      <div className="grid">
        {status.regions.map((r) => (
          <div key={r.name} className={`card ${r.disabled ? "off" : r.healthy && r.circuit === "closed" ? "ok" : "bad"}`}>
            <header>
              <h3>{r.name}</h3>
              <span className="muted">prioridad {r.priority}</span>
            </header>
            <ul className="facts">
              <li>Health check: <strong>{r.healthy ? "sano" : "no sano"}</strong></li>
              <li>
                Circuito: <strong>{r.circuit}</strong>
                {r.circuit === "open" && ` (${r.circuit_open_remaining_s.toFixed(0)} s)`}
              </li>
              <li>En curso: {r.inflight} · TTFT medio: {fmt(r.ewma_ttft_ms)}</li>
              <li>Solicitudes {r.requests} · éxitos {r.successes} · fallas {r.failures}</li>
              {r.last_error && <li className="error small">Último error: {r.last_error}</li>}
            </ul>
            {r.sim_admin_url && (
              <div className="buttons">
                {MODES.map((m) => (
                  <button key={m} className="small" onClick={() => simulate(r, m)}>
                    {MODE_LABEL[m]}
                  </button>
                ))}
              </div>
            )}
            <button className="small secondary" onClick={() => toggle(r)}>
              {r.disabled ? "Reincorporar" : "Retirar de la rotación"}
            </button>
          </div>
        ))}
      </div>
      <label className="muted small">
        Token de administración (si APP_ADMIN_TOKEN está definido):{" "}
        <input type="password" value={token} onChange={(e) => setToken(e.target.value)} className="inline" />
      </label>
      {msg && <p className="muted">{msg}</p>}
    </section>
  );
}

// ------------------------------------------------------------------- lotes
function BatchTab() {
  const [jobs, reload] = usePolling<{ data: Job[] }>("/v1/batches", 2000);
  const [msg, setMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function submit(body: string, description: string) {
    const r = await fetch(`/v1/batches?description=${encodeURIComponent(description)}`, {
      method: "POST",
      headers: { "Content-Type": "application/jsonl" },
      body,
    });
    const data = await r.json();
    setMsg(r.ok ? `Lote ${data.id.slice(0, 14)}… recibido (${data.request_counts.total} solicitudes)` : JSON.stringify(data.detail));
    reload();
  }

  async function upload() {
    const f = fileRef.current?.files?.[0];
    if (f) await submit(await f.text(), f.name);
  }

  async function cancel(id: string) {
    const r = await fetch(`/v1/batches/${id}/cancel`, { method: "POST" });
    setMsg(r.ok ? "Cancelación solicitada" : `HTTP ${r.status}`);
    reload();
  }

  return (
    <section>
      <div className="buttons">
        <button onClick={() => submit(sampleBatch(50), "ejemplo-50")}>Enviar lote de ejemplo (50)</button>
        <input ref={fileRef} type="file" accept=".jsonl,application/jsonl" aria-label="Archivo JSONL" />
        <button className="secondary" onClick={upload}>Subir JSONL</button>
      </div>
      {msg && <p className="muted">{msg}</p>}
      <table>
        <thead>
          <tr>
            <th>Trabajo</th>
            <th>Estado</th>
            <th>Progreso</th>
            <th>Regiones</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {(jobs?.data ?? []).map((j) => {
            const done = j.request_counts.completed + j.request_counts.failed;
            const pct = j.request_counts.total ? (100 * done) / j.request_counts.total : 0;
            return (
              <tr key={j.id}>
                <td title={j.id}>{j.description ?? j.id.slice(0, 14)}</td>
                <td>
                  <span className={`badge ${j.status}`}>{j.status}</span>
                </td>
                <td>
                  <progress max={100} value={pct} /> {done}/{j.request_counts.total}
                  {j.request_counts.failed > 0 && <span className="error small"> ({j.request_counts.failed} fallidas)</span>}
                </td>
                <td className="small">
                  {Object.entries(j.regions_used).map(([k, v]) => `${k}: ${v}`).join(" · ") || "–"}
                </td>
                <td>
                  <div className="actions">
                  {!TERMINAL.has(j.status) && j.status !== "cancelling" && (
                    <button className="small secondary" onClick={() => cancel(j.id)}>Cancelar</button>
                  )}
                  {done > 0 && <a href={`/v1/batches/${j.id}/output`}>resultados</a>}
                  {j.request_counts.failed > 0 && <a href={`/v1/batches/${j.id}/errors`}>errores</a>}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

// -------------------------------------------------------------------- app
export default function App() {
  const [tab, setTab] = useState<Tab>("online");
  const [ready] = usePolling<{ status: string; available_regions: string[] }>("/readyz", 3000);
  return (
    <main>
      <header className="top">
        <div>
          <h1>Gateway multi-región</h1>
          <p className="subtitle">Laboratorio LOC-02 · inferencia online y por lotes con conmutación por falla</p>
        </div>
        <span className={`badge ${ready?.status === "ok" ? "completed" : "failed"}`}>
          {ready ? `${ready.status} · ${ready.available_regions.join(", ") || "sin regiones"}` : "sin conexión"}
        </span>
      </header>
      <nav>
        {(["online", "regiones", "lotes"] as Tab[]).map((t) => (
          <button key={t} className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>
            {t === "online" ? "Online" : t === "regiones" ? "Regiones" : "Lotes"}
          </button>
        ))}
      </nav>
      {tab === "online" && <OnlineTab />}
      {tab === "regiones" && <RegionsTab />}
      {tab === "lotes" && <BatchTab />}
    </main>
  );
}
