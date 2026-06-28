"use client";
import { createContext, useContext, useState, useEffect } from "react";
import type { ComparisonResult, ExtractionResult, VendorResponse } from "@aerchain/shared-types";

interface BuyerState {
  loadedVendors: VendorResponse[];
  extractions: Record<string, ExtractionResult>;
  downgradeReports: Record<string, unknown>;
  comparison: ComparisonResult | null;
  setLoadedVendors: (updater: VendorResponse[] | ((prev: VendorResponse[]) => VendorResponse[])) => void;
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
  const [loadedVendors, setLoadedVendorsState] = useState<VendorResponse[]>(() =>
    hydrateFromSession<VendorResponse[]>("loadedVendors", []),
  );
  const [extractions, setExtractionsState] = useState<Record<string, ExtractionResult>>(() =>
    hydrateFromSession<Record<string, ExtractionResult>>("extractions", {}),
  );
  const [downgradeReports, setDowngradeReportsState] = useState<Record<string, unknown>>(() =>
    hydrateFromSession<Record<string, unknown>>("downgradeReports", {}),
  );
  const [comparison, setComparisonState] = useState<ComparisonResult | null>(() =>
    hydrateFromSession<ComparisonResult | null>("comparison", null),
  );

  // Persist to sessionStorage on each state mutation
  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        sessionStorage.setItem("loadedVendors", JSON.stringify(loadedVendors));
      } catch { /* quota errors are non-fatal */ }
    }
  }, [loadedVendors]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        sessionStorage.setItem("extractions", JSON.stringify(extractions));
      } catch { /* quota errors are non-fatal */ }
    }
  }, [extractions]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        sessionStorage.setItem("downgradeReports", JSON.stringify(downgradeReports));
      } catch { /* quota errors are non-fatal */ }
    }
  }, [downgradeReports]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        sessionStorage.setItem("comparison", JSON.stringify(comparison));
      } catch { /* quota errors are non-fatal */ }
    }
  }, [comparison]);

  // APPEND-BY-DEFAULT: setLoadedVendors appends; use clearVendors() for replacement
  function setLoadedVendors(
    updater: VendorResponse[] | ((prev: VendorResponse[]) => VendorResponse[]),
  ) {
    if (typeof updater === "function") {
      setLoadedVendorsState(updater);
    } else {
      setLoadedVendorsState((prev) => [...prev, ...updater]);
    }
  }

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
        setLoadedVendors,
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
