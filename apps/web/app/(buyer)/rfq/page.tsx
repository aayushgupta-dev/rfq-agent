import type { RFQ } from "@aerchain/shared-types";
import { Card, CardContent, CardHeader, CardTitle, CardAction } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import rfqRaw from "../../../public/data/rfq.json";
import RegenButton from "./regen-button";

// ponytail: Server Component renders committed rfq.json instantly (D-21);
// only the Regen button needs "use client" — isolated to regen-button.tsx.
const rfq = rfqRaw as unknown as RFQ;

function formatBudget(range: number[] | null | undefined): string {
  if (!range || range.length < 2) return "";
  return ` ($${(range[0] / 1000).toFixed(0)}k–$${(range[1] / 1000).toFixed(0)}k)`;
}

export default function RfqPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold leading-tight text-foreground">RFQ Overview</h1>

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle className="text-xl font-semibold leading-tight">{rfq.title}</CardTitle>
            <p className="mt-1 text-xs font-semibold text-muted-foreground">
              {rfq.client_name} &middot; Issued {rfq.issue_date} &middot; Deadline {rfq.response_deadline}
            </p>
          </div>
          <CardAction>
            {/* ponytail: RegenButton is a client island; regen is optional user-triggered call */}
            <RegenButton />
          </CardAction>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-xs font-semibold text-muted-foreground mb-1">
              {rfq.line_items.length} line items in scope
            </p>
            <ul className="list-disc list-inside space-y-0.5">
              {rfq.line_items.map((li) => (
                <li key={li.id} className="text-sm text-foreground">
                  {li.name}
                  {formatBudget(li.budget_range_usd)}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-muted-foreground mb-1">Commercial expectations</p>
            <p className="text-sm text-foreground line-clamp-3">{rfq.commercial_expectations}</p>
          </div>
          {rfq.budget_total_usd && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground">Total budget</p>
              <p className="text-sm text-foreground">${rfq.budget_total_usd.toLocaleString()}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Separator className="my-6" />

      {/* Full structured body */}
      <div className="space-y-6">

        {/* Scope */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-semibold leading-tight">Scope</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground leading-relaxed">{rfq.scope_summary}</p>
          </CardContent>
        </Card>

        {/* Timelines */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-semibold leading-tight">Timelines</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-semibold text-muted-foreground">Issue date</p>
                <p className="text-sm text-foreground">{rfq.issue_date}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-muted-foreground">Response deadline</p>
                <p className="text-sm text-foreground">{rfq.response_deadline}</p>
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold text-muted-foreground mb-2">Per-line-item timelines</p>
              <ul className="space-y-1">
                {rfq.line_items.map((li) => (
                  <li key={li.id} className="flex justify-between text-sm">
                    <span className="text-foreground">{li.name}</span>
                    <span className="text-muted-foreground">
                      {li.timeline_weeks != null ? `${li.timeline_weeks} weeks` : "Not specified"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-semibold leading-tight">Line Items</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {rfq.line_items.map((li) => (
              <div key={li.id} data-testid="rfq-line-item" className="rounded-lg border border-border p-4 space-y-2">
                <div className="flex items-start justify-between gap-4">
                  <p className="text-sm font-semibold text-foreground">{li.name}</p>
                  {li.budget_range_usd && li.budget_range_usd.length >= 2 && (
                    <p className="text-xs font-semibold text-muted-foreground whitespace-nowrap">
                      ${li.budget_range_usd[0].toLocaleString()} – ${li.budget_range_usd[1].toLocaleString()}
                    </p>
                  )}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">{li.description}</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {li.deliverables.map((d, i) => (
                    <li key={i} className="text-xs text-muted-foreground leading-snug">{d}</li>
                  ))}
                </ul>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Commercial Expectations */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-semibold leading-tight">Commercial Expectations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-foreground leading-relaxed">{rfq.commercial_expectations}</p>
          </CardContent>
        </Card>

        {/* Vendor Questionnaire */}
        {rfq.questionnaire && rfq.questionnaire.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-xl font-semibold leading-tight">Vendor Questionnaire</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="list-decimal list-inside space-y-2">
                {rfq.questionnaire.map((q, i) => (
                  <li key={i} className="text-sm text-foreground leading-relaxed">{q}</li>
                ))}
              </ol>
            </CardContent>
          </Card>
        )}

        {/* Compliance Requirements */}
        {rfq.compliance_requirements && rfq.compliance_requirements.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-xl font-semibold leading-tight">Compliance Requirements</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc list-inside space-y-2">
                {rfq.compliance_requirements.map((c, i) => (
                  <li key={i} className="text-sm text-foreground leading-relaxed">{c}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

      </div>
    </div>
  );
}
