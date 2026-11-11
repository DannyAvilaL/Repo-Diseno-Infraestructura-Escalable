// Cliente tipado del gateway. La API key vive SOLO en memoria (estado de React):
// nunca se guarda en localStorage ni se incluye en el bundle.

export interface Timings {
  total_ms: number;
  queue_wait_ms: number;
  ttft_ms: number | null;
  load_ms: number | null;
}

export interface ChatResponse {
  text: string;
  model: string;
  usage: { prompt_tokens: number; completion_tokens: number };
  timings: Timings;
  cache_hit: boolean;
  coalesced: boolean;
  cold_start: boolean;
  instance_id: string;
  flags: string[];
}

export type JobStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED" | "DEAD";

export interface JobView {
  job_id: string;
  status: JobStatus;
  attempts: number;
  result: ChatResponse | null;
  error: string | null;
}

export interface ChatParams {
  prompt: string;
  system?: string;
  temperature: number;
  max_tokens: number;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly retryAfter?: number,
  ) {
    super(message);
  }
}

const BASE = "/api";

function headers(apiKey: string, extra: Record<string, string> = {}): HeadersInit {
  return { "Content-Type": "application/json", "X-API-Key": apiKey, ...extra };
}

async function failure(resp: Response): Promise<never> {
  let detail = resp.statusText;
  try {
    const data = (await resp.json()) as { error?: string; detail?: string };
    detail = data.error ?? data.detail ?? detail;
  } catch {
    /* cuerpo no JSON */
  }
  const ra = resp.headers.get("Retry-After");
  throw new ApiError(resp.status, detail, ra ? Number(ra) : undefined);
}

export async function chat(apiKey: string, params: ChatParams): Promise<ChatResponse> {
  const resp = await fetch(`${BASE}/v1/chat`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify(params),
  });
  if (!resp.ok) return failure(resp);
  return (await resp.json()) as ChatResponse;
}

export async function* chatStream(
  apiKey: string,
  params: ChatParams,
  signal?: AbortSignal,
): AsyncGenerator<string, void, void> {
  const resp = await fetch(`${BASE}/v1/chat/stream`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify(params),
    signal,
  });
  if (!resp.ok || !resp.body) return failure(resp);
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      if (frame.startsWith("event: done")) return;
      if (frame.startsWith("event: error")) throw new ApiError(502, "Error durante el streaming");
      const line = frame.split("\n").find((l) => l.startsWith("data: "));
      if (line) yield (JSON.parse(line.slice(6)) as { token: string }).token;
    }
  }
}

export async function submitJob(
  apiKey: string,
  params: ChatParams,
  idempotencyKey: string,
): Promise<{ job_id: string; idempotent_replay: boolean }> {
  const resp = await fetch(`${BASE}/v1/jobs`, {
    method: "POST",
    headers: headers(apiKey, { "Idempotency-Key": idempotencyKey }),
    body: JSON.stringify(params),
  });
  if (!resp.ok) return failure(resp);
  return (await resp.json()) as { job_id: string; idempotent_replay: boolean };
}

export async function getJob(apiKey: string, jobId: string): Promise<JobView> {
  const resp = await fetch(`${BASE}/v1/jobs/${jobId}`, { headers: headers(apiKey) });
  if (!resp.ok) return failure(resp);
  return (await resp.json()) as JobView;
}

export interface Stats {
  instance_id: string;
  init_seconds: number;
  served: number;
  provider: string;
  model: string;
  cache: { entries: number; hits: number; misses: number; coalesced: number; hit_ratio: number };
  queue_depth: number;
  dead_letters: number;
}

export async function getStats(apiKey: string): Promise<Stats> {
  const resp = await fetch(`${BASE}/v1/stats`, { headers: headers(apiKey) });
  if (!resp.ok) return failure(resp);
  return (await resp.json()) as Stats;
}
