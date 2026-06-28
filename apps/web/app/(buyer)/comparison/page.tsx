"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type {
  AttentionPoint,
  ClarificationQuestion,
  ComparisonResult,
  DimensionComparison,
  ExtractionResult,
  LineItemOffer,
  RFQ,
  VendorReadiness,
} from "@aerchain/shared-types";
import { useBuyerContext } from "@/contexts/BuyerContext";
import { streamCompare, fetchRfq } from "@/lib/api";
import { ComparabilityBadge } from "@/components/comparability-badge";
import { FlagBadge } from "@/components/flag-badge";
import { StreamProgress } from "@/components/stream-progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";

// D-11 comparison phase sequence for progress
const COMPARISON_PHASES: Record<string, number> = {
  align: 20,
  comparability: 40,
  compare: 70,
  clarify: 90,
};

function AttentionPanel({
  attention_points,
  clarification_questions,
}: {
  attention_points?: AttentionPoint[];
  clarification_questions?: ClarificationQuestion[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl font-semibold">
          Needs Attention — {attention_points?.length ?? 0} item(s)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {attention_points && attention_points.length > 0 ? (
          <ul className="space-y-2">
            {attention_points.map((ap, i) => (
              <li key={i} className="border-b border-border pb-2 last:border-0">
                <p className="text-sm font-medium">{ap.summary}</p>
                {ap.dimension_or_field && (
                  <p className="text-xs text-muted-foreground">
                    Field: {ap.dimension_or_field}
                  </p>
                )}
                {ap.vendors_affected && ap.vendors_affected.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    Vendors: {ap.vendors_affected.join(", ")}
                  </p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No attention points flagged.</p>
        )}

        {clarification_questions && clarification_questions.length > 0 && (
          <div>
            <p className="text-sm font-semibold mb-2">Clarification questions</p>
            <ul className="space-y-2">
              {clarification_questions.map((cq, i) => (
                <li key={i} className="border-b border-border pb-2 last:border-0">
                  <p className="text-xs text-muted-foreground">{cq.vendor_name}</p>
                  <p className="text-sm">{cq.question}</p>
                  <p className="text-xs text-muted-foreground">{cq.why_needed}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ComparabilityMatrix({
  vendorNames,
  dimensions,
}: {
  vendorNames: string[];
  dimensions: DimensionComparison[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl font-semibold">Comparability Matrix</CardTitle>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          <div data-testid="comparability-matrix" className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr>
                  {/* Sticky dimension column header */}
                  <th className="text-left py-2 px-3 font-semibold text-muted-foreground w-32">
                    Dimension
                  </th>
                  {/* D-13: stable input order — input sequence preserved */}
                  {vendorNames.map((name) => (
                    <th key={name} className="text-center py-2 px-3 font-semibold">
                      {name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dimensions.map((dim) => (
                  <tr key={dim.dimension} className="border-t border-border">
                    <td className="py-2 px-3 font-medium capitalize text-muted-foreground">
                      {dim.dimension}
                    </td>
                    {vendorNames.map((name) => {
                      const verdict = dim.verdicts.find((v) => v.vendor_name === name);
                      return (
                        <td key={name} className="py-2 px-3 text-center">
                          {verdict ? (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className="inline-block cursor-help">
                                  <ComparabilityBadge verdict={verdict.verdict} />
                                </span>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p className="max-w-xs">{verdict.reason}</p>
                              </TooltipContent>
                            </Tooltip>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </TooltipProvider>

        {/* D-14: code-authority note — always visible */}
        <p className="text-xs text-muted-foreground mt-3">
          Comparability determined in code from evidence — not a model verdict
        </p>
      </CardContent>
    </Card>
  );
}

function ReadinessRow({ readiness }: { readiness: VendorReadiness[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl font-semibold">Data Readiness</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {readiness.map((r) => (
            <div key={r.vendor_name} className="flex items-center gap-3">
              <span className="text-sm font-medium w-40 truncate">{r.vendor_name}</span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="text-sm text-muted-foreground cursor-help">
                      Data readiness: {r.comparable_count}/{r.total_dimensions} dimensions comparable
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    {/* D-13: data-readiness indicator, not a leaderboard position */}
                    <p>Not a ranking or score</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <span className="text-xs text-muted-foreground">{r.descriptor}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function LineItemTable({
  vendorNames,
  offers,
}: {
  vendorNames: string[];
  offers: LineItemOffer[];
}) {
  // Group offers by line item name
  const lineItems = Array.from(new Set(offers.map((o) => o.line_item_name)));

  return (
    <Collapsible>
      <CollapsibleTrigger className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground mb-2">
        Show line-item offers ({lineItems.length} items)
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr>
                <th className="text-left py-2 px-3 font-semibold text-muted-foreground">
                  Line Item
                </th>
                {vendorNames.map((name) => (
                  <th key={name} className="text-center py-2 px-3 font-semibold">
                    {name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {lineItems.map((item) => (
                <tr key={item} className="border-t border-border">
                  <td className="py-2 px-3 font-medium">{item}</td>
                  {vendorNames.map((name) => {
                    const offer = offers.find(
                      (o) => o.line_item_name === item && o.vendor_name === name,
                    );
                    return (
                      <td key={name} className="py-2 px-3 text-center">
                        {offer ? (
                          <div className="flex flex-col items-center gap-1">
                            <span>{offer.pricing_verbatim ?? "—"}</span>
                            {/* pricing_status is a bare str on the server — FlagBadge handles unknown values (WR-03) */}
                            <FlagBadge status={offer.pricing_status} />
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

function DimensionNarratives({ dimensions }: { dimensions: DimensionComparison[] }) {
  return (
    <div className="space-y-2">
      {dimensions.map((dim) => (
        <Collapsible key={dim.dimension}>
          <CollapsibleTrigger className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground">
            Show {dim.dimension} detail
          </CollapsibleTrigger>
          <CollapsibleContent>
            <p className="text-sm mt-1 pl-2 border-l-2 border-border text-muted-foreground">
              {dim.narrative}
            </p>
          </CollapsibleContent>
        </Collapsible>
      ))}
    </div>
  );
}

function ComparisonView({
  comparison,
}: {
  comparison: ComparisonResult;
}) {
  // D-13: stable input order — vendorNames from comparison preserves server input order
  const vendorNames = comparison.vendor_names;

  return (
    <div className="space-y-6">
      {/* D-12 Attention panel — always first (buyer-first hierarchy, UI-06) */}
      <AttentionPanel
        attention_points={comparison.attention_points}
        clarification_questions={comparison.clarification_questions}
      />

      {/* D-11 Comparability matrix — hero */}
      <ComparabilityMatrix vendorNames={vendorNames} dimensions={comparison.dimensions} />

      {/* D-13 Data readiness */}
      {comparison.vendor_readiness && comparison.vendor_readiness.length > 0 && (
        <ReadinessRow readiness={comparison.vendor_readiness} />
      )}

      {/* D-11 Line-item drill-down (Collapsible) */}
      {comparison.line_item_offers && comparison.line_item_offers.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <LineItemTable vendorNames={vendorNames} offers={comparison.line_item_offers} />
          </CardContent>
        </Card>
      )}

      {/* D-11 Per-dimension narratives (Collapsible) */}
      {comparison.dimensions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Dimension Detail</CardTitle>
          </CardHeader>
          <CardContent>
            <DimensionNarratives dimensions={comparison.dimensions} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ComparisonPage() {
  const { extractions, comparison, setComparison } = useBuyerContext();
  const vendorNames = Object.keys(extractions);
  // The fresh extraction list is snapshotted inside each run (effect + manual button)
  // so a run never closes over a stale render's list (CR-02).

  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [rfqError, setRfqError] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [phase, setPhase] = useState("");
  const [progressValue, setProgressValue] = useState(0);
  const [error, setError] = useState<string | null>(null);
  // ponytail: AbortController ref — T-05-06-C mitigate
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchRfq()
      .then((r) => { setRfq(r); setRfqError(false); })
      .catch(() => setRfqError(true)); // WR-05: surface, don't strand silently
  }, []);

  // Abort whatever run is in flight (most relevant to the manual button, whose
  // controller is held in abortRef) on unmount. The auto-start effect aborts its
  // own controller via its cleanup; abort is idempotent so this never double-fires
  // harmfully. (T-05-06-C / WR-01)
  useEffect(() => {
    return () => { abortRef.current?.abort(); };
  }, []);

  // Single source of truth for the comparison SSE consume loop (WR-02 — was
  // duplicated + drifted across the auto-start effect and the manual button).
  // The caller owns the AbortController and a `cancelled` guard so a torn-down
  // run never writes state after its stream was aborted (CR-02/WR-01).
  async function runComparison(
    list: ExtractionResult[],
    activeRfq: RFQ,
    controller: AbortController,
    isCancelled: () => boolean,
  ) {
    setStreaming(true);
    setPhase("");
    setProgressValue(0);
    setError(null);
    try {
      for await (const event of streamCompare(list, activeRfq, controller.signal)) {
        if (isCancelled()) return;
        if (event.type === "status") {
          const { phase: p } = event.payload as { message: string; phase: string };
          setPhase(p);
          const pct = COMPARISON_PHASES[p];
          if (pct !== undefined) setProgressValue(pct);
        }
        if (event.type === "result") {
          // Comparison result is bare ComparisonResult — no normalization needed (asymmetric with extraction)
          setComparison(event.payload as ComparisonResult);
          setProgressValue(100);
          setStreaming(false);
          break; // terminal — stop consuming (CR-02: don't flip to error on a late event)
        }
        if (event.type === "error") {
          setError((event.payload as { message: string }).message);
          setStreaming(false);
          break;
        }
        if (event.type === "done") {
          setStreaming(false);
          break;
        }
      }
    } catch (e) {
      if (!isCancelled() && (e as Error).name !== "AbortError") {
        setError("Connection lost. Check the AI service is running.");
        setStreaming(false);
      }
    }
  }

  // Auto-start comparison when ≥2 extractions available + rfq loaded + not yet cached.
  // CR-02: depend on the actual inputs (rfq + available vendor count) and snapshot the
  // fresh extraction list inside the effect, so the run never closes over a stale list.
  // The effect OWNS its AbortController + `cancelled` guard (WR-01) and aborts on
  // deps-change re-run AND unmount — replacing the previous separate []-deps abort effect.
  useEffect(() => {
    if (comparison) return; // cached (D-02)
    const snapshot = Object.keys(extractions).map((n) => extractions[n]);
    if (snapshot.length < 2 || !rfq) return;

    const controller = new AbortController();
    abortRef.current = controller;
    let cancelled = false;
    void runComparison(snapshot, rfq, controller, () => cancelled);

    return () => { cancelled = true; controller.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rfq, vendorNames.length]); // re-evaluate when the available vendor count changes

  // Empty state: no extractions at all
  if (vendorNames.length === 0) {
    return (
      <div className="p-6 space-y-4">
        <h1 className="text-3xl font-bold">Vendor Comparison</h1>
        <Alert>
          <AlertDescription>
            Run extraction on at least one vendor before comparing.{" "}
            <Link href="/extraction" className="underline font-medium">
              Go to Extraction
            </Link>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Empty state: not enough vendors for comparison (server enforces _MIN_VENDORS=2)
  if (vendorNames.length === 1) {
    return (
      <div className="p-6 space-y-4">
        <h1 className="text-3xl font-bold">Vendor Comparison</h1>
        <Alert variant="default">
          <AlertDescription>
            Load at least 2 vendors to compare. Go to Vendor Input to load another vendor.{" "}
            <Button asChild variant="outline" size="sm" className="mt-2">
              <Link href="/input">Go to Vendor Input</Link>
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Vendor Comparison</h1>

      {streaming && (
        <div className="space-y-4">
          <StreamProgress phase={phase} value={progressValue} />
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-6 w-full my-2" />
          ))}
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>Comparison could not complete. {error}</AlertDescription>
        </Alert>
      )}

      {/* WR-05: RFQ fetch failed — surface it instead of leaving the screen inert */}
      {rfqError && !comparison && (
        <Alert variant="destructive">
          <AlertDescription>
            Could not load the RFQ — check the AI service is running, then reload this page.
          </AlertDescription>
        </Alert>
      )}

      {!comparison && !streaming && !error && (
        <div className="flex items-center gap-4">
          <p className="text-sm text-muted-foreground">
            {vendorNames.length} vendors ready.
          </p>
          <Button
            onClick={() => {
              // Manual trigger if auto-start was skipped (e.g. rfq loaded after render).
              // Snapshot the fresh list here (CR-02) and reuse the shared loop (WR-02).
              if (!rfq || streaming) return;
              const snapshot = vendorNames.map((n) => extractions[n]);
              if (snapshot.length < 2) return;
              const controller = new AbortController();
              abortRef.current = controller;
              void runComparison(snapshot, rfq, controller, () => controller.signal.aborted);
            }}
          >
            Run Comparison
          </Button>
        </div>
      )}

      {comparison && <ComparisonView comparison={comparison} />}
    </div>
  );
}
