import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  chat,
  chatStream,
  getJob,
  getStats,
  submitJob,
  type ChatParams,
  type ChatResponse,
  type Stats,
} from "./api";
import { Badges } from "./components/Badges";
import { HistoryTable, type HistoryRow } from "./components/HistoryTable";

type Mode = "sync" | "stream" | "job";

const MODE_HELP: Record<Mode, string> = {
  sync: "Petición/respuesta (API Gateway → Lambda / Cloud Run). Simple, pero acotada por timeouts.",
  stream: "Streaming SSE: mejora el TTFT percibido; dificulta el filtrado de salida.",
  job: "Asíncrono con cola: 202 + polling. Desacopla el pico de carga (SQS / Service Bus / Pub/Sub).",
};

export default function App() {
  const [apiKey, setApiKey] = useState("dev-key-change-me");
  const [mode, setMode] = useState<Mode>("sync");
  const [prompt, setPrompt] = useState("Explica qué es un cold start en arquitecturas serverless.");
  const [temperature, setTemperature] = useState(0);
  const [maxTokens, setMaxTokens] = useState(128);
  const [busy, setBusy] = useState(false);
  const [output, setOutput] = useState("");
  const [last, setLast] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const params = (): ChatParams => ({ prompt, temperature, max_tokens: maxTokens });

  const refreshStats = useCallback(async () => {
    try {
      setStats(await getStats(apiKey));
    } catch {
      setStats(null);
    }
  }, [apiKey]);

  useEffect(() => {
    void refreshStats();
  }, [refreshStats]);

  const record = (label: Mode, r: ChatResponse) =>
    setRows((prev) => [
      { id: prev.length + 1, mode: label, ms: r.timings.total_ms, cache: r.cache_hit || r.coalesced, cold: r.cold_start, instance: r.instance_id },
      ...prev,
    ]);

  const run = async () => {
    setBusy(true);
    setError(null);
    setOutput("");
    setLast(null);
    abortRef.current = new AbortController();
    try {
      if (mode === "sync") {
        const r = await chat(apiKey, params());
        setOutput(r.text);
        setLast(r);
        record("sync", r);
      } else if (mode === "stream") {
        const started = performance.now();
        let first: number | null = null;
        for await (const token of chatStream(apiKey, params(), abortRef.current.signal)) {
          first ??= performance.now() - started;
          setOutput((o) => o + token);
        }
        setRows((prev) => [
          { id: prev.length + 1, mode: "stream", ms: performance.now() - started, ttft: first ?? undefined, cache: false, cold: false, instance: "-" },
          ...prev,
        ]);
      } else {
        const idem = crypto.randomUUID();
        const { job_id } = await submitJob(apiKey, params(), idem);
        setOutput(`Trabajo ${job_id} aceptado (202). Consultando estado…`);
        for (let i = 0; i < 120; i++) {
          await new Promise((res) => setTimeout(res, 500));
          const view = await getJob(apiKey, job_id);
          setOutput(`Trabajo ${job_id}: ${view.status} (intentos: ${view.attempts})`);
          if (view.status === "SUCCEEDED" && view.result) {
            setOutput(view.result.text);
            setLast(view.result);
            record("job", view.result);
            break;
          }
          if (view.status === "DEAD") throw new ApiError(500, view.error ?? "El trabajo fue a la DLQ");
        }
      }
    } catch (e) {
      if (e instanceof ApiError) {
        setError(`HTTP ${e.status}: ${e.message}${e.retryAfter ? ` (reintentar en ${e.retryAfter}s)` : ""}`);
      } else if ((e as Error).name !== "AbortError") {
        setError((e as Error).message);
      }
    } finally {
      setBusy(false);
      void refreshStats();
    }
  };

  // Ráfaga: N peticiones concurrentes para observar caché, cold start y backpressure (429).
  const burst = async (n: number) => {
    setBusy(true);
    setError(null);
    const results = await Promise.allSettled(
      Array.from({ length: n }, (_, i) => chat(apiKey, { prompt: `${prompt} #${i % 5}`, temperature: 0, max_tokens: maxTokens })),
    );
    const ok = results.filter((r): r is PromiseFulfilledResult<ChatResponse> => r.status === "fulfilled");
    ok.forEach((r) => record("sync", r.value));
    const limited = results.length - ok.length;
    setOutput(`Ráfaga de ${n}: ${ok.length} OK, ${limited} rechazadas (429/errores).`);
    setBusy(false);
    void refreshStats();
  };

  return (
    <main>
      <header>
        <h1>Consola Serverless LLM</h1>
        <p className="sub">Sesión 5 · Diseño de Infraestructura Escalable para LLMs</p>
      </header>

      <section className="grid">
        <div className="card">
          <label>
            API key (solo en memoria)
            <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} autoComplete="off" />
          </label>
          <div className="modes" role="tablist">
            {(["sync", "stream", "job"] as Mode[]).map((m) => (
              <button key={m} role="tab" aria-selected={mode === m} className={mode === m ? "active" : ""} onClick={() => setMode(m)}>
                {m === "sync" ? "Síncrono" : m === "stream" ? "Streaming" : "Asíncrono (cola)"}
              </button>
            ))}
          </div>
          <p className="hint">{MODE_HELP[mode]}</p>
          <label>
            Prompt
            <textarea rows={4} value={prompt} onChange={(e) => setPrompt(e.target.value)} />
          </label>
          <div className="row">
            <label>
              Temperatura: {temperature.toFixed(1)}
              <input type="range" min={0} max={1.5} step={0.1} value={temperature} onChange={(e) => setTemperature(Number(e.target.value))} />
            </label>
            <label>
              Máx. tokens
              <input type="number" min={1} max={4096} value={maxTokens} onChange={(e) => setMaxTokens(Number(e.target.value))} />
            </label>
          </div>
          <p className="hint">Con temperatura 0 la respuesta es cacheable; con &gt; 0 no se cachea.</p>
          <div className="row">
            <button className="primary" disabled={busy || !prompt.trim()} onClick={() => void run()}>
              {busy ? "Procesando…" : "Enviar"}
            </button>
            <button disabled={busy} onClick={() => void burst(20)}>
              Ráfaga ×20
            </button>
            <button disabled={!busy} onClick={() => abortRef.current?.abort()}>
              Cancelar
            </button>
          </div>
        </div>

        <div className="card">
          <h2>Respuesta</h2>
          {error && <p className="error" role="alert">{error}</p>}
          <pre className="output">{output || "—"}</pre>
          {last && <Badges r={last} />}
          {stats && (
            <dl className="stats">
              <dt>Instancia</dt><dd>{stats.instance_id} · atendió {stats.served}</dd>
              <dt>Init</dt><dd>{stats.init_seconds}s ({stats.provider}/{stats.model})</dd>
              <dt>Caché</dt><dd>{stats.cache.entries} entradas · hit ratio {(stats.cache.hit_ratio * 100).toFixed(0)}%</dd>
              <dt>Cola</dt><dd>{stats.queue_depth} pendientes · {stats.dead_letters} en DLQ</dd>
            </dl>
          )}
        </div>
      </section>

      <HistoryTable rows={rows} />
    </main>
  );
}
