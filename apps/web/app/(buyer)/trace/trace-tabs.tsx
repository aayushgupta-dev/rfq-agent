"use client";

import { useState, useCallback } from "react";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { TraceData, ClampEntry, DowngradeEntry } from "./page";

// "not_comparable" → "Not Comparable", "technical" → "Technical". Used for the diff
// tables so internal dimension keys / verdict enums never surface as raw snake_case.
function titleCase(s: string): string {
  return s.replace(/[_-]+/g, " ").trim().replace(/\b\w/g, (c) => c.toUpperCase());
}

// Reasons embed verdict enums (e.g. "technical ceiling=not_comparable for X").
// Title-case the snake_case verdict tokens so no raw enum shows in the reason text.
function humanizeReason(reason: string): string {
  return reason.replace(/\b(not_comparable|partially|comparable)\b/g, (m) => titleCase(m));
}

// Pipeline stage: a numbered step in the trace timeline
function Stage({
  number,
  title,
  children,
}: {
  number: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-semibold text-foreground">
          {number}
        </div>
        {number < 4 && <div className="mt-1 w-px flex-1 bg-border" />}
      </div>
      <div className="pb-6 min-w-0 flex-1">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
          {title}
        </p>
        {children}
      </div>
    </div>
  );
}

// Input summary for extraction traces
function ExtractionInput({ input }: { input: Record<string, unknown> }) {
  const vendorName = input.vendor_name as string | undefined;
  const sourceId = input.source_id as string | undefined;
  return (
    <p className="text-sm text-foreground">
      <span className="font-semibold">{vendorName ?? "unknown vendor"}</span>
      {sourceId && (
        <span className="text-muted-foreground ml-2 text-xs">(source: {sourceId})</span>
      )}
    </p>
  );
}

// Input summary for comparison traces
function ComparisonInput({ input }: { input: Record<string, unknown> }) {
  const vendorNames = input.vendor_names as string[] | undefined;
  const rfqTitle = input.rfq_title as string | undefined;
  return (
    <div className="space-y-1">
      {rfqTitle && <p className="text-sm text-foreground">{rfqTitle}</p>}
      {vendorNames && (
        <p className="text-xs text-muted-foreground">
          Vendors: {vendorNames.join(", ")}
        </p>
      )}
    </div>
  );
}

// Downgrade diff for extraction traces
function DowngradeDiff({ entries }: { entries: DowngradeEntry[] }) {
  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No overrides — model output matched grounding constraints.
      </p>
    );
  }
  return (
    <div
      data-testid="trace-diff"
      className="rounded-lg border bg-card p-4 space-y-3"
    >
      <p className="text-sm font-semibold text-foreground">
        Code overruled the model on {entries.length} verdict(s)
      </p>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b text-muted-foreground">
            <th className="text-left py-1 pr-3 font-semibold">Field</th>
            <th className="text-left py-1 pr-3 font-semibold">Model value</th>
            <th className="text-left py-1 font-semibold">Final status</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e, i) => (
            <tr key={i} className="bg-amber-50 border-b last:border-0">
              <td className="py-2 pr-3 font-mono">{e.field_name}</td>
              <td className="py-2 pr-3">{titleCase(String(e.model_value))}</td>
              <td className="py-2">{titleCase(e.final_status)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Clamp diff for comparison traces
function ClampDiff({ entries }: { entries: ClampEntry[] }) {
  const changed = entries.filter((e) => e.model_proposed !== e.clamped_to);
  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No overrides — model output matched grounding constraints.
      </p>
    );
  }
  return (
    <div
      data-testid="trace-diff"
      className="rounded-lg border bg-card p-4 space-y-3"
    >
      <p className="text-sm font-semibold text-foreground">
        Code overruled the model on {changed.length} verdict(s)
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="text-left py-1 pr-3 font-semibold">Vendor</th>
              <th className="text-left py-1 pr-3 font-semibold">Dimension</th>
              <th className="text-left py-1 pr-3 font-semibold">Model proposed</th>
              <th className="text-left py-1 pr-3 font-semibold">Clamped to</th>
              <th className="text-left py-1 font-semibold">Reason</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => {
              const wasChanged = e.model_proposed !== e.clamped_to;
              return (
                <tr
                  key={i}
                  className={`border-b last:border-0 ${wasChanged ? "bg-amber-50" : ""}`}
                >
                  <td className="py-2 pr-3 font-mono">{e.vendor_name}</td>
                  <td className="py-2 pr-3">{titleCase(e.dimension)}</td>
                  <td className="py-2 pr-3">{titleCase(e.model_proposed)}</td>
                  <td className="py-2 pr-3">{titleCase(e.clamped_to)}</td>
                  <td className="py-2 text-muted-foreground">{humanizeReason(e.ceiling_reason)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [text]);
  return (
    <button
      onClick={handleCopy}
      className="text-xs text-muted-foreground hover:text-foreground border rounded px-2 py-1 transition-colors"
    >
      {copied ? "Copied" : "Copy raw output"}
    </button>
  );
}

function TracePanel({ trace }: { trace: TraceData }) {
  const rawStr = JSON.stringify(trace.raw_model_output, null, 2);
  const rawPreview = rawStr.slice(0, 300);

  return (
    <div className="space-y-6 pt-4">
      {/* Pipeline timeline */}
      <div>
        <h3 className="text-xl font-semibold leading-tight text-foreground mb-4">
          Pipeline
        </h3>
        <div>
          {/* Stage 1: Input */}
          <Stage number={1} title="Input">
            {trace.kind === "extraction" ? (
              <ExtractionInput input={trace.input} />
            ) : (
              <ComparisonInput input={trace.input} />
            )}
          </Stage>

          {/* Stage 2: Prompt */}
          <Stage number={2} title="Prompt">
            <div className="space-y-1">
              <p className="text-sm text-foreground">
                <span className="font-mono text-xs font-semibold">
                  {trace.resolved_prompt.id}
                </span>{" "}
                <span className="text-xs text-muted-foreground">
                  v{trace.resolved_prompt.version}
                </span>
              </p>
              <a
                href="#prompt-pack"
                className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2"
              >
                View prompt in Prompt Pack ↓
              </a>
            </div>
          </Stage>

          {/* Stage 3: Raw model output */}
          <Stage number={3} title="Raw model output">
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">
                {rawPreview}
                {rawStr.length > 300 && "…"}
              </p>
              <ScrollArea className="h-48 rounded-md border bg-muted p-3">
                <pre className="font-mono text-xs whitespace-pre-wrap break-words">
                  {rawStr}
                </pre>
              </ScrollArea>
              <CopyButton text={rawStr} />
            </div>
          </Stage>

          {/* Stage 4: Grounded/clamped final */}
          <Stage number={4} title="Grounded / clamped final">
            {trace.kind === "extraction" ? (
              <p className="text-sm text-foreground">
                <span className="font-semibold">
                  {(trace.input.vendor_name as string) ?? "Vendor"}
                </span>{" "}
                — extraction complete
                {typeof trace.grounding_step?.fields_downgraded === "number" && (
                  <span className="text-xs text-muted-foreground ml-2">
                    ({trace.grounding_step.fields_downgraded} field(s) downgraded by
                    grounding gate)
                  </span>
                )}
              </p>
            ) : (
              <p className="text-sm text-foreground">
                Comparison complete —{" "}
                {
                  ((trace.input.vendor_names as string[]) ?? []).length
                }{" "}
                vendors across 6 dimensions
              </p>
            )}
          </Stage>
        </div>
      </div>

      {/* Downgrade / clamp diff — the "code disproves model" proof */}
      <div>
        <h3 className="text-xl font-semibold leading-tight text-foreground mb-3">
          Code vs. Model
        </h3>
        {trace.kind === "extraction" ? (
          <DowngradeDiff
            entries={trace.grounding_step?.downgrade_report?.entries ?? []}
          />
        ) : (
          <ClampDiff entries={trace.clamp_step?.entries ?? []} />
        )}
      </div>
    </div>
  );
}

export function TraceTabs({ traces }: { traces: TraceData[] }) {
  return (
    <Tabs defaultValue={traces[0]?.name ?? ""} data-testid="trace-tabs">
      <TabsList className="flex flex-wrap gap-1 h-auto w-full justify-start">
        {traces.map((t) => (
          <TabsTrigger key={t.name} value={t.name}>
            {t.displayName}
          </TabsTrigger>
        ))}
      </TabsList>
      {traces.map((t) => (
        <TabsContent key={t.name} value={t.name}>
          <TracePanel trace={t} />
        </TabsContent>
      ))}
    </Tabs>
  );
}
