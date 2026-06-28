interface EvidenceSnippetProps {
  snippet?: string;
}

// D-07: snippet shown inline. When absent, renders "No verified source" — never
// implies evidence exists. (IN-02: dropped the "Show in context" disclosure — it
// expanded to the identical snippet text; the Evidence contract carries no separate
// surrounding-passage source to reveal, so the affordance added nothing.)
export function EvidenceSnippet({ snippet }: EvidenceSnippetProps) {
  return (
    <p data-testid="evidence-snippet" className="text-xs text-muted-foreground px-2 py-1">
      <span className="font-semibold">Source:</span>{" "}
      {snippet ? snippet : <em className="text-slate-400">No verified source</em>}
    </p>
  );
}
