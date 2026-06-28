"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { ExtractionResult, FieldStr, FlagStatus, RFQ } from "@aerchain/shared-types";
import { useBuyerContext } from "@/contexts/BuyerContext";
import { streamExtract, normalizeExtractionPayload } from "@/lib/api";
// ponytail: extraction grounds vendors against the SAME committed RFQ the /rfq overview
// shows and the samples were written for. Importing the static fixture (not /data/rfq,
// which live-regenerates a fresh RFQ via the model on every visit) makes the flow
// instant, deterministic, and correct — vendors are never compared to a different RFQ.
import rfqRaw from "../../../public/data/rfq.json";
import { EvidenceSnippet } from "@/components/evidence-snippet";
import { FlagBadge } from "@/components/flag-badge";
import { StreamProgress } from "@/components/stream-progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

// The committed procurement event — stable module-level reference (matches /rfq page).
const rfq = rfqRaw as unknown as RFQ;

// Human-readable streaming phases (the SSE emits raw keys "model" / "grounding").
const PHASE_LABELS: Record<string, string> = {
  model: "Reading the proposal and extracting fields…",
  grounding: "Verifying every extracted fact against the vendor's own words…",
};

// D-09 category layout — maps to ExtractionResult field paths
const CATEGORIES: { label: string; key: keyof ExtractionResult }[] = [
  { label: "Scope", key: "scope_summary" },
  { label: "Pricing", key: "pricing_structure" },
  { label: "Pricing", key: "total_price" },
  { label: "Commercial Terms", key: "commercial_terms" },
  { label: "Timeline", key: "timeline" },
  { label: "Compliance", key: "compliance_points" },
  { label: "Assumptions", key: "assumptions" },
  { label: "Exclusions", key: "exclusions" },
  { label: "Risks", key: "risks" },
];

// D-08 severity order for Gaps & Risks panel
const SEVERITY: FlagStatus[] = ["missing", "conflicting", "unclear", "unsupported"];

interface FlaggedField {
  label: string;
  status: FlagStatus;
}

function collectFlaggedFields(extraction: ExtractionResult): FlaggedField[] {
  const items: FlaggedField[] = [];

  function checkField(label: string, field: FieldStr | undefined) {
    if (field && field.status !== "present") {
      items.push({ label, status: field.status });
    }
  }

  checkField("Scope summary", extraction.scope_summary);
  checkField("Pricing structure", extraction.pricing_structure);
  checkField("Total price", extraction.total_price);
  checkField("Commercial terms", extraction.commercial_terms);
  checkField("Timeline", extraction.timeline);

  extraction.compliance_points?.forEach((f, i) => checkField(`Compliance point ${i + 1}`, f));
  extraction.assumptions?.forEach((f, i) => checkField(`Assumption ${i + 1}`, f));
  extraction.exclusions?.forEach((f, i) => checkField(`Exclusion ${i + 1}`, f));
  extraction.risks?.forEach((f, i) => checkField(`Risk ${i + 1}`, f));
  extraction.line_items?.forEach((li) => {
    checkField(`${li.line_item_name} — pricing`, li.pricing);
    checkField(`${li.line_item_name} — scope coverage`, li.scope_coverage);
  });

  // Sort by severity: missing → conflicting → unclear → unsupported
  items.sort((a, b) => SEVERITY.indexOf(a.status) - SEVERITY.indexOf(b.status));
  return items;
}

function FieldRow({ label, field }: { label: string; field: FieldStr }) {
  // Evidence over assertion (§1/§8): surface the grounded span for any field that
  // carries one — not only `present`. For `conflicting`, each value in field.values[]
  // carries its OWN evidence (ConflictingValueStr), so render per-value with its source;
  // never label a grounded conflicting value "No verified source".
  const directEvidence = field.evidence?.length ? field.evidence[0] : undefined;
  const isConflicting = field.status === "conflicting" && !!field.values?.length;
  return (
    <div className="grid grid-cols-[auto_1fr] gap-2 py-2 border-b border-border last:border-0">
      <div className="flex items-center gap-1.5">
        <span className="text-xs font-semibold text-muted-foreground">{label}</span>
        <FlagBadge status={field.status} />
      </div>
      <div>
        {isConflicting ? (
          field.values!.map((v, i) => {
            const ev = v.evidence?.length ? v.evidence[0] : undefined;
            return (
              <div key={i} className="mb-1 last:mb-0">
                <p className="text-sm">{v.value ?? "—"}</p>
                <EvidenceSnippet snippet={ev?.snippet} />
              </div>
            );
          })
        ) : (
          <>
            <p className="text-sm">{field.value ?? "—"}</p>
            <EvidenceSnippet snippet={directEvidence?.snippet} />
          </>
        )}
      </div>
    </div>
  );
}

function CategoryCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ExtractionView({ extraction }: { extraction: ExtractionResult }) {
  const flagged = collectFlaggedFields(extraction);

  return (
    <div className="space-y-4">
      {/* D-08 Gaps & Risks panel — always visible, buyer-first */}
      <Card data-testid="gaps-panel">
        <CardHeader>
          <CardTitle className="text-xl font-semibold">
            Gaps &amp; Risks — {flagged.length} issue(s)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {flagged.length === 0 ? (
            <p className="text-sm text-muted-foreground">All fields present — no gaps detected.</p>
          ) : (
            <ul className="space-y-1">
              {flagged.map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-sm">
                  <span>{f.label}</span>
                  <FlagBadge status={f.status} />
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* D-09 Category sections */}
      <div data-testid="extraction-result" className="space-y-4">
        {/* Scope */}
        <CategoryCard title="Scope">
          <FieldRow label="Scope summary" field={extraction.scope_summary} />
          {extraction.line_items?.map((li) => (
            <div key={li.line_item_id} className="mt-2">
              <p className="text-xs font-semibold text-muted-foreground mb-1">{li.line_item_name}</p>
              <FieldRow label="Scope coverage" field={li.scope_coverage} />
            </div>
          ))}
        </CategoryCard>

        {/* Pricing */}
        <CategoryCard title="Pricing">
          <FieldRow label="Pricing structure" field={extraction.pricing_structure} />
          <FieldRow label="Total price" field={extraction.total_price} />
          {extraction.line_items?.map((li) => (
            <div key={li.line_item_id} className="mt-2">
              <p className="text-xs font-semibold text-muted-foreground mb-1">{li.line_item_name}</p>
              <FieldRow label="Pricing" field={li.pricing} />
            </div>
          ))}
        </CategoryCard>

        {/* Commercial Terms */}
        <CategoryCard title="Commercial Terms">
          <FieldRow label="Commercial terms" field={extraction.commercial_terms} />
        </CategoryCard>

        {/* Timeline */}
        <CategoryCard title="Timeline">
          <FieldRow label="Timeline" field={extraction.timeline} />
        </CategoryCard>

        {/* Compliance */}
        <CategoryCard title="Compliance">
          {extraction.compliance_points?.length ? (
            extraction.compliance_points.map((f, i) => (
              <FieldRow key={i} label={`Point ${i + 1}`} field={f} />
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No compliance data extracted.</p>
          )}
        </CategoryCard>

        {/* Assumptions */}
        <CategoryCard title="Assumptions">
          {extraction.assumptions?.length ? (
            extraction.assumptions.map((f, i) => (
              <FieldRow key={i} label={`Assumption ${i + 1}`} field={f} />
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No assumptions extracted.</p>
          )}
        </CategoryCard>

        {/* Exclusions */}
        <CategoryCard title="Exclusions">
          {extraction.exclusions?.length ? (
            extraction.exclusions.map((f, i) => (
              <FieldRow key={i} label={`Exclusion ${i + 1}`} field={f} />
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No exclusions extracted.</p>
          )}
        </CategoryCard>

        {/* Risks */}
        <CategoryCard title="Risks">
          {extraction.risks?.length ? (
            extraction.risks.map((f, i) => (
              <FieldRow key={i} label={`Risk ${i + 1}`} field={f} />
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No risks extracted.</p>
          )}
        </CategoryCard>
      </div>
    </div>
  );
}

export default function ExtractionPage() {
  const { loadedVendors, extractions, setExtraction, setDowngradeReport } = useBuyerContext();
  const [selectedVendor, setSelectedVendor] = useState<string>("");
  const [streaming, setStreaming] = useState(false);
  const [phase, setPhase] = useState("");
  const [progressValue, setProgressValue] = useState(0);
  const [error, setError] = useState<string | null>(null);
  // ponytail: AbortController ref — T-05-06-C mitigate (SSE stream that never closes)
  const abortRef = useRef<AbortController | null>(null);

  // Set initial vendor selection (RFQ is the committed fixture — no fetch needed)
  useEffect(() => {
    if (!selectedVendor && loadedVendors.length > 0) {
      setSelectedVendor(loadedVendors[0].vendor_name);
    }
  }, [loadedVendors, selectedVendor]);

  // Session cache check + SSE trigger.
  // The effect OWNS its AbortController: the cleanup aborts this run's request on
  // unmount AND on deps-change re-run. A `cancelled` guard prevents a torn-down run
  // (e.g. React strict-mode's mount→cleanup→mount, or a fast tab switch) from writing
  // state after its stream was aborted. (T-05-06-C)
  useEffect(() => {
    if (!selectedVendor || !rfq) return;
    if (extractions[selectedVendor]) return; // cached — render instantly (D-02)

    const vendor = loadedVendors.find((v) => v.vendor_name === selectedVendor);
    if (!vendor) return;

    const controller = new AbortController();
    abortRef.current = controller;
    let cancelled = false;
    setStreaming(true);
    setPhase("");
    setProgressValue(0);
    setError(null);

    (async () => {
      try {
        for await (const event of streamExtract(vendor, rfq, controller.signal)) {
          if (cancelled) return;
          if (event.type === "status") {
            const { phase: p } = event.payload as { message: string; phase: string };
            setPhase(PHASE_LABELS[p] ?? p);
            // D-25: drive progress from known phase sequence, not a +20% counter
            if (p === "model") setProgressValue(40);
            if (p === "grounding") setProgressValue(80);
          }
          if (event.type === "result") {
            const { result, downgrade_report } = normalizeExtractionPayload(
              event.payload as Record<string, unknown>,
            );
            setExtraction(selectedVendor, result);
            setDowngradeReport(selectedVendor, downgrade_report);
            setProgressValue(100);
            setStreaming(false);
            break; // terminal — a late error must not flip the cached extraction to an error state (WR-04)
          }
          if (event.type === "error") {
            setError((event.payload as { message: string }).message);
            setStreaming(false);
            break;
          }
          if (event.type === "done") { setStreaming(false); break; }
        }
      } catch (e) {
        if (!cancelled && (e as Error).name !== "AbortError") {
          setError("Connection lost. Check the AI service is running.");
          setStreaming(false);
        }
      }
    })();

    return () => { cancelled = true; controller.abort(); };
  }, [selectedVendor, rfq]); // eslint-disable-line react-hooks/exhaustive-deps

  const extraction = selectedVendor ? extractions[selectedVendor] : undefined;

  // No vendors loaded
  if (loadedVendors.length === 0) {
    return (
      <div className="p-6 space-y-4">
        <h1 className="text-3xl font-bold">Extraction Review</h1>
        <Alert>
          <AlertDescription>
            Select or load a vendor on the{" "}
            <Link href="/input" className="underline font-medium">Input screen</Link>{" "}
            to begin extraction.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Extraction Review</h1>

      {/* D-10: vendor selector Tabs */}
      <Tabs
        data-testid="vendor-tabs"
        value={selectedVendor}
        onValueChange={(v) => {
          setError(null);
          setSelectedVendor(v);
        }}
      >
        <TabsList>
          {loadedVendors.map((v) => (
            <TabsTrigger key={v.vendor_name} value={v.vendor_name}>
              {v.vendor_name}
            </TabsTrigger>
          ))}
        </TabsList>

        {loadedVendors.map((v) => (
          <TabsContent key={v.vendor_name} value={v.vendor_name}>
            {streaming && v.vendor_name === selectedVendor && (
              <div className="space-y-4">
                <StreamProgress phase={phase} value={progressValue} />
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-6 w-full my-2" />
                ))}
              </div>
            )}

            {error && v.vendor_name === selectedVendor && (
              <Alert variant="destructive" data-testid="extraction-error">
                <AlertDescription>
                  Extraction could not complete. {error} — Try reloading or check the AI service is running.
                </AlertDescription>
              </Alert>
            )}

            {extraction && v.vendor_name === selectedVendor && !streaming && (
              <ExtractionView extraction={extraction} />
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
