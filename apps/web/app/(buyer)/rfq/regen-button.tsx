"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { fetchRfq } from "@/lib/api";

// ponytail: only this component needs "use client"; page.tsx stays a Server Component
export default function RegenButton() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRegen() {
    setLoading(true);
    setError(null);
    try {
      await fetchRfq();
      // ponytail: page is a Server Component; on success we reload to pick up new data
      window.location.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Regeneration failed");
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        variant="outline"
        disabled={loading}
        onClick={handleRegen}
        className="shrink-0"
      >
        {loading ? "Regenerating..." : "Regenerate RFQ"}
      </Button>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
