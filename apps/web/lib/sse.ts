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
    // SSE events are separated by a blank line. The server (sse-starlette) uses
    // \r\n line endings, so the delimiter is \r\n\r\n — handle that AND plain \n\n.
    // Chunks may straddle read() calls (Pitfall 1), so keep the trailing partial.
    const parts = buf.split(/\r\n\r\n|\n\n/);
    buf = parts.pop() ?? "";
    for (const part of parts) {
      // An event may carry multiple data: lines (joined with \n per the SSE spec);
      // ": ..." comment lines (keep-alive pings) are ignored.
      const data = part
        .split(/\r\n|\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).replace(/^ /, ""))
        .join("\n");
      if (data) yield JSON.parse(data) as EventEnvelope;
    }
  }
}
