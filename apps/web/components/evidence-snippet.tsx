"use client";
import * as React from "react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";

interface EvidenceSnippetProps {
  snippet?: string;
  sourcePassage?: string;
}

// D-07: snippet always visible inline; Collapsible opens source passage
// When snippet is absent, renders "No verified source" — never implies evidence exists
export function EvidenceSnippet({ snippet, sourcePassage }: EvidenceSnippetProps) {
  return (
    <Collapsible>
      <p data-testid="evidence-snippet" className="text-xs text-muted-foreground px-2 py-1">
        <span className="font-semibold">Source:</span>{" "}
        {snippet ? snippet : <em className="text-slate-400">No verified source</em>}
      </p>
      {sourcePassage && snippet && (
        <>
          <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
            <ChevronDown className="size-3" /> Show in context
          </CollapsibleTrigger>
          <CollapsibleContent>
            {/* Highlighted span uses --primary border (UI-SPEC Color §) */}
            <p className="text-xs border-l-2 border-primary pl-2 mt-1">{sourcePassage}</p>
          </CollapsibleContent>
        </>
      )}
    </Collapsible>
  );
}
