import { useState } from "react";

type Metrics = {
  ttft_ms: number | null;
  e2e_ms: number;
  tpot_ms: number | null;
  completion_tokens: number | null;
  prompt_tokens: number | null;
  tokens_per_second: number | null;
};

type Turn = { role: "user" | "assistant"; content: string; metrics?: Metrics };

// Lee el flujo SSE de /v1/chat/stream con fetch (EventSource no admite POST).
async function streamChat(
  messages: Turn[],
  onToken: (text: string) => void,
  onMetrics: (m: Metrics) => void,
): Promise<void> {
  const response = await fetch("/v1/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: messages.map(({ role, content }) => ({ role, content })) }),
  });
  if (!response.ok || !response.body) {
    const detail = await response.text();
    throw new Error(`HTTP ${response.status}: ${detail}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const raw of events) {
      const event = raw.match(/^event: (.*)$/m)?.[1];
      const data = raw.match(/^data: (.*)$/m)?.[1];
      if (!event || !data) continue;
      const payload = JSON.parse(data);
      if (event === "token") onToken(payload.text);
      else if (event === "metrics") onMetrics(payload);
      else if (event === "error") throw new Error(payload.detail);
    }
  }
}

function MetricsBar({ m }: { m: Metrics }) {
  const fmt = (v: number | null, unit: string) => (v === null ? "—" : `${v.toFixed(0)} ${unit}`);
  return (
    <div className="metrics">
      <span>TTFT {fmt(m.ttft_ms, "ms")}</span>
      <span>TPOT {fmt(m.tpot_ms, "ms")}</span>
      <span>Total {fmt(m.e2e_ms, "ms")}</span>
      <span>{m.tokens_per_second === null ? "—" : `${m.tokens_per_second.toFixed(1)} tok/s`}</span>
      <span>
        Tokens {m.prompt_tokens ?? "?"} in / {m.completion_tokens ?? "?"} out
      </span>
    </div>
  );
}

export default function App() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const question = input.trim();
    if (!question || busy) return;
    setError(null);
    setBusy(true);
    setInput("");
    const history: Turn[] = [...turns, { role: "user", content: question }];
    setTurns([...history, { role: "assistant", content: "" }]);
    try {
      await streamChat(
        history,
        (text) =>
          setTurns((prev) => {
            const last = prev[prev.length - 1];
            return [...prev.slice(0, -1), { ...last, content: last.content + text }];
          }),
        (metrics) =>
          setTurns((prev) => [...prev.slice(0, -1), { ...prev[prev.length - 1], metrics }]),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setTurns(history);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Asistente universitario</h1>
      <p className="subtitle">Laboratorio LOC-01 · inferencia local con métricas por respuesta</p>
      <section className="chat">
        {turns.map((t, i) => (
          <article key={i} className={t.role}>
            <div>{t.content || (busy && i === turns.length - 1 ? "…" : "")}</div>
            {t.metrics && <MetricsBar m={t.metrics} />}
          </article>
        ))}
      </section>
      {error && <p className="error">Error: {error}</p>}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pregunte por un trámite o reglamento…"
          maxLength={4000}
          disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()}>
          {busy ? "Generando…" : "Enviar"}
        </button>
      </form>
    </main>
  );
}
