"use client";
import { createContext, useContext, useState, useEffect, type Dispatch, type SetStateAction } from "react";
import type { ComparisonResult, ExtractionResult, VendorResponse } from "@aerchain/shared-types";

interface BuyerState {
  loadedVendors: VendorResponse[];
  extractions: Record<string, ExtractionResult>;
  downgradeReports: Record<string, unknown>;
  comparison: ComparisonResult | null;
  // IN-04: standard setState contract — callers decide append vs replace explicitly.
  // (Previously a split append-array / replace-via-function setter whose array branch
  // no real caller exercised; all callers use the functional form.)
  setLoadedVendors: Dispatch<SetStateAction<VendorResponse[]>>;
  clearVendors: () => void;
  setExtraction: (name: string, result: ExtractionResult) => void;
  setDowngradeReport: (name: string, report: unknown) => void;
  setComparison: (result: ComparisonResult | null) => void;
}

const BuyerContext = createContext<BuyerState | null>(null);

// ponytail: sessionStorage is tab-scoped; correct for a single-buyer prototype (Pitfall 6)
function hydrateFromSession<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function BuyerProvider({ children }: { children: React.ReactNode }) {
  // SSR-safe: first client render must match the server (empty), so we DON'T read
  // sessionStorage during render. We rehydrate in a post-mount effect below.
  // Reading sessionStorage in the useState initializer caused a hydration mismatch
  // (server renders empty, client renders stored data) that regenerated the tree.
  const [loadedVendors, setLoadedVendorsState] = useState<VendorResponse[]>([]);
  const [extractions, setExtractionsState] = useState<Record<string, ExtractionResult>>({});
  const [downgradeReports, setDowngradeReportsState] = useState<Record<string, unknown>>({});
  const [comparison, setComparisonState] = useState<ComparisonResult | null>(null);
  const [hydrated, setHydrated] = useState(false);

  // Rehydrate from sessionStorage once, after mount (post-hydration).
  useEffect(() => {
    // SSR-safe: reading sessionStorage in the initializer caused a hydration mismatch (see note above).
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional post-mount rehydrate
    setLoadedVendorsState(hydrateFromSession<VendorResponse[]>("loadedVendors", []));
    setExtractionsState(hydrateFromSession<Record<string, ExtractionResult>>("extractions", {}));
    setDowngradeReportsState(hydrateFromSession<Record<string, unknown>>("downgradeReports", {}));
    setComparisonState(hydrateFromSession<ComparisonResult | null>("comparison", null));
    setHydrated(true);
  }, []);

  // Persist to sessionStorage on each state mutation.
  // Gated on `hydrated` so the initial empty state never clobbers stored data
  // before rehydration runs.
  useEffect(() => {
    if (!hydrated) return;
    try {
      sessionStorage.setItem("loadedVendors", JSON.stringify(loadedVendors));
    } catch { /* quota errors are non-fatal */ }
  }, [loadedVendors, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    try {
      sessionStorage.setItem("extractions", JSON.stringify(extractions));
    } catch { /* quota errors are non-fatal */ }
  }, [extractions, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    try {
      sessionStorage.setItem("downgradeReports", JSON.stringify(downgradeReports));
    } catch { /* quota errors are non-fatal */ }
  }, [downgradeReports, hydrated]);

  useEffect(() => {
    if (!hydrated) return;
    try {
      sessionStorage.setItem("comparison", JSON.stringify(comparison));
    } catch { /* quota errors are non-fatal */ }
  }, [comparison, hydrated]);

  function clearVendors() {
    setLoadedVendorsState([]);
  }

  function setExtraction(name: string, result: ExtractionResult) {
    setExtractionsState((prev) => ({ ...prev, [name]: result }));
  }

  function setDowngradeReport(name: string, report: unknown) {
    setDowngradeReportsState((prev) => ({ ...prev, [name]: report }));
  }

  function setComparison(result: ComparisonResult | null) {
    setComparisonState(result);
  }

  return (
    <BuyerContext.Provider
      value={{
        loadedVendors,
        extractions,
        downgradeReports,
        comparison,
        setLoadedVendors: setLoadedVendorsState,
        clearVendors,
        setExtraction,
        setDowngradeReport,
        setComparison,
      }}
    >
      {children}
    </BuyerContext.Provider>
  );
}

export function useBuyerContext(): BuyerState {
  const ctx = useContext(BuyerContext);
  if (!ctx) throw new Error("useBuyerContext must be used within BuyerProvider");
  return ctx;
}
