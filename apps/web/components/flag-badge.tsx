import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { FlagStatus } from "@aerchain/shared-types";

// UI-SPEC Color § flag badge palette — absence is first-class (§8)
const flagVariants: Record<FlagStatus, string> = {
  present: "bg-green-100 text-green-800",
  missing: "bg-red-100 text-red-800",
  unclear: "bg-amber-100 text-amber-800",
  conflicting: "bg-orange-100 text-orange-800",
  unsupported: "bg-slate-100 text-slate-600",
};

// Neutral fallback so an unknown server status (e.g. a bare `str` pricing_status of
// "bundled" / "not_applicable") still renders as a visible, labelled badge rather than
// an unstyled raw string — absence/flag state stays surfaced, never silently degraded (§8).
const UNKNOWN_VARIANT = "bg-slate-100 text-slate-600";

// Title-case the raw status for display: "not-comparable" → "Not Comparable",
// "missing" → "Missing". data-status keeps the raw value so selectors/tests are unaffected.
function toTitleCase(status: string): string {
  return status
    .replace(/[-_]+/g, " ")
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// Accept `string` (not just FlagStatus): LineItemOffer.pricing_status is a bare str on
// the server, so callers must not force-cast it. Known statuses get their palette; any
// other value falls back to the neutral variant and renders its literal label (WR-03).
export function FlagBadge({ status }: { status: FlagStatus | string }) {
  const variant = flagVariants[status as FlagStatus] ?? UNKNOWN_VARIANT;
  return (
    <Badge
      data-testid="flag-badge"
      data-status={status}
      className={cn("px-2 py-1 text-xs font-semibold whitespace-nowrap", variant)}
    >
      {toTitleCase(status)}
    </Badge>
  );
}
