import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { ComparabilityVerdict } from "@aerchain/shared-types";

// UI-SPEC Color § comparability badge palette
const comparabilityVariants: Record<ComparabilityVerdict, string> = {
  comparable: "bg-primary text-primary-foreground",
  partially: "bg-amber-100 text-amber-800",
  not_comparable: "bg-red-100 text-red-800",
};

export function ComparabilityBadge({ verdict }: { verdict: ComparabilityVerdict }) {
  return (
    <Badge className={cn("px-2 py-1 text-xs font-semibold", comparabilityVariants[verdict])}>
      {verdict.replace("_", " ")}
    </Badge>
  );
}
