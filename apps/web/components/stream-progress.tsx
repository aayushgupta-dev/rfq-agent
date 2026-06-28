import * as React from "react";
import { Progress } from "@/components/ui/progress";

interface StreamProgressProps {
  phase: string;
  value: number;
}

// D-25: full-width, no horizontal padding (UI-SPEC Spacing § streaming progress bar)
// value is pre-computed by caller from phase sequence: "model"→40%, "grounding"→80%, done→100%
export function StreamProgress({ phase, value }: StreamProgressProps) {
  return (
    <div className="space-y-1">
      <p className="text-xs text-muted-foreground">{phase}</p>
      <Progress value={value} className="w-full" />
    </div>
  );
}
