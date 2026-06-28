import fs from "fs/promises";
import path from "path";
import { TraceTabs } from "./trace-tabs";

// ponytail: Server Component — reads public/traces/ at request time; no runtime state needed.
// TraceTabs is "use client" only for tab switching interactivity.

export interface ClampEntry {
  vendor_name: string;
  dimension: string;
  model_proposed: string;
  code_ceiling: string;
  clamped_to: string;
  ceiling_reason: string;
}

export interface DowngradeEntry {
  field_name: string;
  model_value: string;
  final_status: string;
}

export interface ResolvedPrompt {
  id: string;
  version: number;
  system_message_excerpt?: string;
  system_message?: string;
  human_message_template?: string;
}

export interface TraceData {
  name: string; // filename without .json
  displayName: string;
  kind: "comparison" | "extraction";
  input: Record<string, unknown>;
  resolved_prompt: ResolvedPrompt;
  raw_model_output: unknown;
  // comparison traces
  clamp_step?: { entries: ClampEntry[] };
  // extraction traces
  grounding_step?: {
    fields_downgraded?: number;
    downgrade_report?: { entries: DowngradeEntry[] };
  };
  final_result: unknown;
}

// IN-05: single source of truth for both canonical order and display label — keyed on
// the filename stem (no .json). Insertion order defines the canonical trace order; any
// file not listed sorts after these and falls back to an underscored-to-spaces label.
const TRACE_LABELS: Record<string, string> = {
  comparison_trace_1: "Comparison 1",
  comparison_trace_2: "Comparison 2",
  trace_vendor_thorough: "Vendor: Thorough",
  trace_vendor_cheap: "Vendor: Cheap",
  trace_vendor_fluff: "Vendor: Fluff",
  trace_adversarial_fixture: "Adversarial",
};

function displayName(filename: string): string {
  const base = filename.replace(/\.json$/, "");
  return TRACE_LABELS[base] ?? base.replace(/_/g, " ");
}

async function loadTraces(): Promise<TraceData[]> {
  const dir = path.join(process.cwd(), "public", "traces");
  const files = await fs.readdir(dir);
  const jsonFiles = files.filter((f) => f.endsWith(".json"));
  // Canonical order derived from TRACE_LABELS insertion order (comparison traces first —
  // most narrative-rich for demo — then extraction). No separate hand-synced literal list.
  const order = Object.keys(TRACE_LABELS).map((stem) => `${stem}.json`);
  const sorted = [
    ...order.filter((n) => jsonFiles.includes(n)),
    ...jsonFiles.filter((n) => !order.includes(n)),
  ];

  return Promise.all(
    sorted.map(async (file) => {
      const raw = await fs.readFile(path.join(dir, file), "utf-8");
      const data = JSON.parse(raw) as Record<string, unknown>;
      const kind: "comparison" | "extraction" = file.startsWith("comparison_")
        ? "comparison"
        : "extraction";
      return {
        name: file.replace(/\.json$/, ""),
        displayName: displayName(file),
        kind,
        input: data.input as Record<string, unknown>,
        resolved_prompt: data.resolved_prompt as ResolvedPrompt,
        raw_model_output: data.raw_model_output,
        clamp_step: data.clamp_step as TraceData["clamp_step"],
        grounding_step: data.grounding_step as TraceData["grounding_step"],
        final_result: data.final_result,
      };
    }),
  );
}

// Static prompt pack — derived from registry.py frontmatter; embedded as const for a Server
// Component (avoids shelling out to Python at build time). ponytail: static const correct here.
const PROMPT_PACK = [
  {
    id: "rfq-gen",
    version: 1,
    intent:
      "Generate one realistic marketing-services RFQ covering 8 line items with scope, timelines, commercial expectations, a vendor questionnaire, and compliance requirements.",
    docs_url: "docs/prompts/rfq-gen.md",
  },
  {
    id: "vendor-gen",
    version: 1,
    intent:
      "Generate a single vendor response to a given RFQ — deliberately realistic and messy, with varying completeness, pricing structures, and clarity.",
    docs_url: "docs/prompts/vendor-gen.md",
  },
  {
    id: "messy-data-gen",
    version: 1,
    intent:
      "Issue-type taxonomy (8 mess types) embedded in vendor-gen; defines how to inject real-world complexity (missing pricing, partial scope, vague timelines) that stresses extraction and comparison agents.",
    docs_url: "docs/prompts/messy-data-gen.md",
  },
  {
    id: "ui-ux-gen",
    version: 1,
    intent:
      "Generate buyer-facing UI structure, dashboard section layouts, comparison view organisation, and UX copy for the five buyer screens.",
    docs_url: "docs/prompts/ui-ux-gen.md",
  },
  {
    id: "extraction",
    version: 1,
    intent:
      "Read a single vendor response and produce a structured ExtractionResult with per-field evidence snippets and missing/unclear/conflicting/unsupported flags. Never fills missing info.",
    docs_url: "docs/prompts/extraction.md",
  },
  {
    id: "comparison",
    version: 1,
    intent:
      "Compare ExtractionResult objects across six dimensions. Establishes comparability before any ranking; surfaces which vendors are comparable and which require further information.",
    docs_url: "docs/prompts/comparison.md",
  },
  {
    id: "clarification",
    version: 1,
    intent:
      "Given flagged fields (missing/unclear/conflicting/unsupported), draft specific, actionable clarification questions the buyer can send to the vendor, each tied to a specific flagged field.",
    docs_url: "docs/prompts/clarification.md",
  },
];

export default async function TracePage() {
  const traces = await loadTraces();

  return (
    <div className="space-y-8">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold leading-tight text-foreground">
          Prompt Trace
        </h1>
        <p className="text-sm text-muted-foreground">
          Input → Prompt → Raw model output → Grounded/clamped final
        </p>
      </div>

      {/* Section 1: Trace tabs */}
      <TraceTabs traces={traces} />

      {/* Section 2: Prompt Pack list */}
      <div className="rounded-lg border bg-card p-6 space-y-4">
        <h2 className="text-xl font-semibold leading-tight text-foreground">
          Prompt Pack — 7 prompts
        </h2>
        <ul className="divide-y divide-border">
          {PROMPT_PACK.map((p) => (
            <li key={p.id} className="py-3 flex flex-col gap-1">
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-foreground font-mono">
                  {p.id}
                </span>
                <span className="text-xs text-muted-foreground">
                  v{p.version}
                </span>
              </div>
              <p className="text-sm text-foreground">{p.intent}</p>
              <a
                href={`/${p.docs_url}`}
                className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2 w-fit"
              >
                {p.docs_url}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
