import { Markdown } from "@/components/markdown";

interface EvidenceSnippetProps {
  snippet?: string;
  // The displayed field value. When the grounded snippet is verbatim-equal to it
  // (the model quotes the source word-for-word), repeating the whole snippet under
  // the value is pure duplication — collapse it to a compact "grounded" marker.
  value?: string;
}

// Normalize for the verbatim-equality check: trim + collapse internal whitespace so a
// stray newline/space difference doesn't defeat the dedupe.
function norm(s: string): string {
  return s.replace(/\s+/g, " ").trim();
}

// D-07: evidence is first-class and never implies a source that isn't there.
//  - No snippet            → "No verified source" (absence stays explicit).
//  - Snippet == value      → "✓ Grounded — verbatim from vendor response" (no duplicate text).
//  - Snippet adds context  → render the source span (as markdown, not raw syntax).
export function EvidenceSnippet({ snippet, value }: EvidenceSnippetProps) {
  if (!snippet) {
    return (
      <p data-testid="evidence-snippet" className="text-xs text-muted-foreground px-2 py-1">
        <span className="font-semibold">Source:</span>{" "}
        <em className="text-slate-400">No verified source</em>
      </p>
    );
  }

  const verbatim = value !== undefined && norm(snippet) === norm(value);
  if (verbatim) {
    return (
      <p
        data-testid="evidence-snippet"
        data-grounded="verbatim"
        className="flex items-center gap-1 text-xs text-emerald-700 px-2 py-1"
      >
        <span aria-hidden>✓</span> Grounded — verbatim from vendor response
      </p>
    );
  }

  return (
    <div data-testid="evidence-snippet" className="text-xs text-muted-foreground px-2 py-1">
      <span className="font-semibold">Source:</span>
      <Markdown className="mt-0.5">{snippet}</Markdown>
    </div>
  );
}
