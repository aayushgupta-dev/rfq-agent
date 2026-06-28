"use client";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { VendorResponse } from "@aerchain/shared-types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { StreamProgress } from "@/components/stream-progress";
import { useBuyerContext } from "@/contexts/BuyerContext";

// ponytail: static JSON imports are resolved at build time — no fetch, no spinner
import thorough from "../../../public/data/vendor_thorough.json";
import cheap from "../../../public/data/vendor_cheap.json";
import fluff from "../../../public/data/vendor_fluff.json";

const BASE = process.env.NEXT_PUBLIC_AI_BASE_URL ?? "http://localhost:8000";
// Mirror the server's 20 MB cap (services/ai/api/app.py /extract/file-text) so a large
// file is rejected client-side instead of uploading fully then failing with 413 (WR-07).
const MAX_UPLOAD_BYTES = 20_000_000;

interface SampleCard {
  id: "thorough" | "cheap" | "fluff";
  label: string;
  vendor: VendorResponse;
  description: string;
}

const SAMPLES: SampleCard[] = [
  {
    id: "thorough",
    label: "Thorough But Pricey",
    vendor: thorough as unknown as VendorResponse,
    description: "Comprehensive scope with bundled pricing that refuses to split line items — comparability blocker.",
  },
  {
    id: "cheap",
    label: "Cheap But Incomplete",
    vendor: cheap as unknown as VendorResponse,
    description: "Aggressive pricing with missing timelines, skipped compliance sections, and vague deliverables.",
  },
  {
    id: "fluff",
    label: "Polished Fluff",
    vendor: fluff as unknown as VendorResponse,
    description: "Beautifully written — no concrete numbers, conflicting claims, and unsupported assurances throughout.",
  },
];

export default function InputPage() {
  const router = useRouter();
  const { loadedVendors, setLoadedVendors } = useBuyerContext();

  // WR-06: guard post-await state writes / navigation after the component unmounts
  // (user navigates away while a paste/upload fetch is in flight).
  const mountedRef = useRef(true);
  useEffect(() => {
    return () => { mountedRef.current = false; };
  }, []);

  // Paste path state
  const [vendorName, setVendorName] = useState("");
  const [rawText, setRawText] = useState("");
  const [pasteLoading, setPasteLoading] = useState(false);
  const [pasteError, setPasteError] = useState<string | null>(null);
  const [pastePhase, setPastePhase] = useState("");

  // Upload path state
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadVendorName, setUploadVendorName] = useState("");
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadPhase, setUploadPhase] = useState("");
  const [weakExtraction, setWeakExtraction] = useState(false);

  // SECTION 1: Sample load (D-04)
  function handleLoadSample(sample: SampleCard) {
    // APPEND — not replace (Plan 05-03 API contract)
    setLoadedVendors((prev) => [...prev, sample.vendor]);
    router.push("/extraction");
  }

  // SECTION 2: Paste path (D-06)
  async function handlePasteSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!vendorName.trim()) return;
    setPasteLoading(true);
    setPasteError(null);
    setPastePhase("Submitting...");
    try {
      const res = await fetch(`${BASE}/input/raw-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vendor_name: vendorName.trim(), raw_text: rawText }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const vendorResponse = (await res.json()) as VendorResponse;
      if (!mountedRef.current) return; // WR-06: don't write state / navigate after unmount
      setLoadedVendors((prev) => [...prev, vendorResponse]);
      router.push("/extraction");
    } catch (err) {
      if (!mountedRef.current) return;
      setPasteError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      if (mountedRef.current) {
        setPasteLoading(false);
        setPastePhase("");
      }
    }
  }

  // SECTION 3: File upload path (D-05)
  async function handleFileExtract(e: React.FormEvent) {
    e.preventDefault();
    if (!uploadFile || !uploadVendorName.trim()) return;
    // WR-07: pre-check the server's 20 MB limit before uploading the whole file
    if (uploadFile.size > MAX_UPLOAD_BYTES) {
      setUploadError("File too large — max 20 MB.");
      return;
    }
    setUploadLoading(true);
    setUploadError(null);
    setWeakExtraction(false);
    setUploadPhase("Extracting text...");
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      const extractRes = await fetch(`${BASE}/extract/file-text`, {
        method: "POST",
        body: formData,
      });
      if (!extractRes.ok) {
        // WR-07: map the server's 20 MB limit (413) to a human message
        if (extractRes.status === 413) throw new Error("File too large — max 20 MB.");
        throw new Error(`HTTP ${extractRes.status}`);
      }
      const { text, chars } = (await extractRes.json()) as { text: string; chars: number };
      if (!mountedRef.current) return; // WR-06
      if (chars < 200) {
        setWeakExtraction(true);
        setUploadLoading(false);
        setUploadPhase("");
        return;
      }
      setUploadPhase("Wrapping vendor response...");
      const wrapRes = await fetch(`${BASE}/input/raw-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vendor_name: uploadVendorName.trim(), raw_text: text }),
      });
      if (!wrapRes.ok) throw new Error(`HTTP ${wrapRes.status}`);
      const vendorResponse = (await wrapRes.json()) as VendorResponse;
      if (!mountedRef.current) return; // WR-06
      setLoadedVendors((prev) => [...prev, vendorResponse]);
      router.push("/extraction");
    } catch (err) {
      if (!mountedRef.current) return;
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      if (mountedRef.current) {
        setUploadLoading(false);
        setUploadPhase("");
      }
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-semibold leading-tight text-foreground">Vendor Input</h1>

      {/* SECTION 1: Hero — one-click sample load (D-04) */}
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Load a sample vendor response to see extraction in action — or paste / upload your own below.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {SAMPLES.map((sample) => (
            <Card key={sample.id} data-testid={`vendor-card-${sample.id}`}>
              <CardHeader>
                <CardTitle className="text-xl font-semibold leading-tight">{sample.label}</CardTitle>
                <CardDescription className="text-xs font-semibold text-muted-foreground leading-snug">
                  {sample.vendor.persona}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground leading-relaxed">{sample.description}</p>
                <Button
                  className="w-full"
                  onClick={() => handleLoadSample(sample)}
                >
                  Load Sample
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Min-vendor notice: only when exactly 1 vendor loaded */}
        {loadedVendors.length === 1 && (
          <Alert>
            <AlertDescription>
              Load at least 2 vendors to use the Comparison screen.
            </AlertDescription>
          </Alert>
        )}

        {/* Empty state: no vendors loaded yet */}
        {loadedVendors.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No vendors loaded yet. Load a sample above or paste a response below.
          </p>
        )}
      </div>

      {/* SECTION 2: Paste path (D-06) */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold leading-tight text-foreground">Paste Vendor Response</h2>
        <form onSubmit={handlePasteSubmit} className="space-y-3">
          <Input
            placeholder="Vendor name"
            value={vendorName}
            onChange={(e) => setVendorName(e.target.value)}
            required
            disabled={pasteLoading}
          />
          <Textarea
            rows={8}
            placeholder="Paste vendor response (text, Markdown, or JSON)..."
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            disabled={pasteLoading}
          />
          {pasteLoading && <StreamProgress phase={pastePhase} value={50} />}
          {pasteError && (
            <Alert variant="destructive">
              <AlertDescription>{pasteError}</AlertDescription>
            </Alert>
          )}
          <Button type="submit" disabled={pasteLoading || !vendorName.trim()}>
            Submit for Extraction
          </Button>
        </form>
      </div>

      {/* SECTION 3: File upload path (D-05) */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold leading-tight text-foreground">Upload Vendor File</h2>
        <form onSubmit={handleFileExtract} className="space-y-3">
          <Input
            placeholder="Vendor name"
            value={uploadVendorName}
            onChange={(e) => setUploadVendorName(e.target.value)}
            required
            disabled={uploadLoading}
          />
          {/* Hidden file input — D-05 accepts PDF/DOCX/XLSX/PPTX */}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.xlsx,.pptx"
            className="hidden"
            onChange={(e) => {
              setUploadFile(e.target.files?.[0] ?? null);
              setWeakExtraction(false);
            }}
          />
          {/* Visible drop zone */}
          <div
            className="border-dashed border-2 border-border rounded-lg p-8 text-center cursor-pointer hover:bg-card transition-colors"
            onClick={() => fileRef.current?.click()}
          >
            {uploadFile ? (
              <p className="text-sm text-foreground">{uploadFile.name}</p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Click or drag a file (PDF, Word, Excel, PPT)
              </p>
            )}
          </div>
          {weakExtraction && (
            <Alert>
              <AlertDescription>
                Text extraction returned very little content — paste the vendor response manually for best results.
              </AlertDescription>
            </Alert>
          )}
          {uploadLoading && <StreamProgress phase={uploadPhase} value={50} />}
          {uploadError && (
            <Alert variant="destructive">
              <AlertDescription>{uploadError}</AlertDescription>
            </Alert>
          )}
          {uploadFile && (
            <Button
              type="submit"
              disabled={uploadLoading || !uploadVendorName.trim()}
            >
              Extract & Analyze
            </Button>
          )}
        </form>
      </div>
    </div>
  );
}
