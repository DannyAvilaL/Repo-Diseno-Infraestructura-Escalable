import { useCallback, useEffect, useRef, useState } from "react";
import { fetchReady, GatewayError, streamChat } from "./api.js";

const fmt = (v, unit = "s") => (v == null ? "—" : `${v.toFixed(2)} ${unit}`);

export default function App() {
  const [prompt, setPrompt] = useState("Explica en pocas frases por qué un balanceador L7 es útil para LLMs.");
  const [apiKey, setApiKey] = useState("");
  const [answer, setAnswer] = useState("");
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(null);
  const [burst, setBurst] = useState(null);
  const abortRef = useRef(null);

  useEffect(() => {
    const check = () => fetchReady().then(setReady).catch(() => setReady(false));
    check();
    const t = setInterval(check, 10000);
    return () => clearInterval(t);
  }, []);

  const send = useCallback(async () => {
    setBusy(true); setError(""); setAnswer(""); setStats(null);
    abortRef.current = new AbortController();
    try {
      await streamChat({
        messages: [{ role: "user", content: prompt }],
        apiKey,
        signal: abortRef.current.signal,
        onToken: (t) => setAnswer((a) => a + t),
        onDone: setStats,
      });
    } catch (e) {
      if (e.name === "AbortError") return;
      setError(e instanceof GatewayError ? `${e.message}${e.retryAfter ? ` Reintente en ${e.retryAfter}s.` : ""}` : "No se pudo contactar el gateway.");
    } finally {
      setBusy(false);
    }
  }, [prompt, apiKey]);

  // Genera N solicitudes simultáneas para observar cola, 429 y 503 (conecta con la teoría de backpressure).
  const stress = useCallback(async (n) => {
    setBurst({ n, ok: 0, rejected: 0, failed: 0, done: false });
    const one = async () => {
      try {
        await streamChat({
          messages: [{ role: "user", content: "Responde en una frase: ¿qué es autoscaling?" }],
          apiKey, maxTokens: 48, onToken: () => {}, onDone: () => {},
        });
        setBurst((b) => ({ ...b, ok: b.ok + 1 }));
      } catch (e) {
        const rejected = e instanceof GatewayError && (e.status === 429 || e.status === 503);
        setBurst((b) => ({ ...b, rejected: b.rejected + (rejected ? 1 : 0), failed: b.failed + (rejected ? 0 : 1) }));
      }
    };
    await Promise.all(Array.from({ length: n }, one));
    setBurst((b) => ({ ...b, done: true }));
  }, [apiKey]);

  return (
    <main>
      <header>
        <h1>LLM Gateway <small>Sesión 4 · Redes, Almacenamiento y Autoscaling</small></h1>
        <span className={`pill ${ready === null ? "" : ready ? "ok" : "bad"}`}>
          {ready === null ? "comprobando…" : ready ? "modelo listo" : "no listo (readiness 503)"}
        </span>
      </header>

      <label>Prompt
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={4} maxLength={16000} />
      </label>
      <label>API key (opcional)
        <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} autoComplete="off" />
      </label>

      <div className="row">
        <button onClick={send} disabled={busy || !prompt.trim()}>{busy ? "Generando…" : "Enviar"}</button>
        <button className="secondary" onClick={() => abortRef.current?.abort()} disabled={!busy}>Cancelar</button>
        <button className="secondary" onClick={() => stress(12)} disabled={burst && !burst.done}>Ráfaga de 12 solicitudes</button>
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      {answer && <pre className="answer">{answer}</pre>}

      {stats && (
        <dl className="stats">
          <div><dt>Espera en cola</dt><dd>{fmt(stats.timings.queue_wait_s)}</dd></div>
          <div><dt>TTFT</dt><dd>{fmt(stats.timings.ttft_s)}</dd></div>
          <div><dt>TPOT</dt><dd>{fmt(stats.timings.tpot_s && stats.timings.tpot_s * 1000, "ms")}</dd></div>
          <div><dt>Latencia e2e</dt><dd>{fmt(stats.timings.e2e_s)}</dd></div>
          <div><dt>Tokens (in/out)</dt><dd>{stats.usage.input_tokens} / {stats.usage.output_tokens}</dd></div>
        </dl>
      )}

      {burst && (
        <p className="burst">
          Ráfaga ({burst.n}): <b>{burst.ok}</b> atendidas · <b>{burst.rejected}</b> rechazadas (429/503) · <b>{burst.failed}</b> errores
          {burst.done ? " — terminada" : " — en curso…"}
        </p>
      )}
    </main>
  );
}
