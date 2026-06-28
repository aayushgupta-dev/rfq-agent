// lib/sse.ts — ponytail: one generic parser handles all SSE endpoints
export type EventEnvelope = { type: string; payload: unknown };

export async function* streamSSE(
  url: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncGenerator<EventEnvelope> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    // SSE lines: "data: <json>\n\n" — chunks may straddle read() calls (Pitfall 1)
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const part of parts) {
      if (part.startsWith("data: ")) {
        yield JSON.parse(part.slice(6)) as EventEnvelope;
      }
    }
  }
}
