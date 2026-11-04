// Cliente del gateway. Consume SSE con fetch (EventSource no permite POST ni headers personalizados).

export class GatewayError extends Error {
  constructor(status, message, retryAfter) {
    super(message);
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

const ERRORS = {
  401: "API key inválida o ausente.",
  422: "Solicitud inválida.",
  429: "Capacidad agotada (cola llena): el sistema aplicó load shedding.",
  502: "Fallo del servidor de inferencia.",
  503: "Tiempo de espera en cola excedido.",
};

export async function streamChat({ messages, apiKey, maxTokens = 256, signal, onToken, onDone }) {
  const res = await fetch("/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(apiKey ? { "X-API-Key": apiKey } : {}) },
    body: JSON.stringify({ messages, stream: true, max_tokens: maxTokens }),
    signal,
  });
  if (!res.ok) {
    throw new GatewayError(res.status, ERRORS[res.status] || `HTTP ${res.status}`, res.headers.get("Retry-After"));
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const event = /^event: (.+)$/m.exec(frame)?.[1];
      const data = /^data: (.+)$/m.exec(frame)?.[1];
      if (!event || !data) continue;
      const payload = JSON.parse(data);
      if (event === "token") onToken(payload.text);
      else if (event === "done") onDone(payload);
      else if (event === "error") throw new GatewayError(502, ERRORS[502]);
    }
  }
}

export async function fetchReady() {
  const res = await fetch("/api/readyz");
  return res.ok;
}
