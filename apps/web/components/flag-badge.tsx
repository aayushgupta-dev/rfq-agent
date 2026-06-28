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

export function FlagBadge({ status }: { status: FlagStatus }) {
  return (
    <Badge
      data-testid="flag-badge"
      data-status={status}
      className={cn("px-2 py-1 text-xs font-semibold", flagVariants[status])}
    >
      {status}
    </Badge>
  );
}
