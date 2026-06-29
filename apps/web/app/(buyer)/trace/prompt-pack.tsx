"use client";
import { useState } from "react";
import { Markdown } from "@/components/markdown";

// `||` (not `??`): an empty-string env var must fall back too — an empty BASE
// silently turns every call into a relative URL that 404s on the web origin.
const BASE = process.env.NEXT_PUBLIC_AI_BASE_URL || "http://localhost:8000";

export interface PromptMeta {
  id: string;
  version: number;
  intent: string;
}

// The full prompt body is fetched from the AI service on expand (GET /prompts/{id}) —
// single source of truth in services/ai/prompts/, never copied into the web app.
export function PromptPack({ prompts }: { prompts: PromptMeta[] }) {
  return (
    <ul className="divide-y divide-border">
      {prompts.map((p) => (
        <PromptItem key={p.id} prompt={p} />
      ))}
    </ul>
  );
}

function PromptItem({ prompt }: { prompt: PromptMeta }) {
  const [open, setOpen] = useState(false);
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function toggle() {
    const next = !open;
    setOpen(next);
    // Fetch once, lazily, on first expand.
    if (next && content === null && !loading) {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${BASE}/prompts/${prompt.id}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as { content: string };
        setContent(data.content);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load prompt");
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <li className="py-3 flex flex-col gap-1">
      <div className="flex items-center gap-3">
        <span className="text-xs font-semibold text-foreground font-mono">{prompt.id}</span>
        <span className="text-xs text-muted-foreground">v{prompt.version}</span>
      </div>
      <p className="text-sm text-foreground">{prompt.intent}</p>
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2 w-fit"
      >
        {open ? "Hide full prompt ↑" : "View full prompt ↓"}
      </button>
      {open && (
        <div className="mt-2 rounded-md border border-border bg-muted/30 p-3">
          {loading && <p className="text-xs text-muted-foreground">Loading prompt…</p>}
          {error && (
            <p className="text-xs text-destructive">
              Could not load prompt — {error}. Check the AI service is running.
            </p>
          )}
          {content && <Markdown className="text-sm">{content}</Markdown>}
        </div>
      )}
    </li>
  );
}
