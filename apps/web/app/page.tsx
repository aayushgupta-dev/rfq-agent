import Link from "next/link";
import { Button } from "@/components/ui/button";

const PIPELINE = [
  { n: "01", title: "RFQ Overview", blurb: "The procurement event — scope, items, timelines, compliance." },
  { n: "02", title: "Vendor Input", blurb: "Paste or upload messy vendor responses, any format." },
  { n: "03", title: "Extraction", blurb: "Every fact carries a source snippet; gaps are flagged." },
  { n: "04", title: "Comparison", blurb: "Who is actually comparable, surfaced side by side." },
  { n: "05", title: "Prompt Trace", blurb: "Every prompt and model output, fully auditable." },
];

export default function Home() {
  return (
    <main className="relative min-h-screen bg-aura overflow-hidden">
      <div className="bg-grid absolute inset-0 -z-10" aria-hidden />

      {/* Brand row */}
      <header className="mx-auto max-w-6xl px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/aerchain-wordmark.png" alt="Aerchain" className="h-5 w-auto" />
          <span className="hidden sm:inline-block h-4 w-px bg-border" aria-hidden />
          <span className="hidden sm:inline eyebrow">Bid Desk</span>
        </div>
        <Button asChild variant="ghost" size="sm">
          <Link href="/trace">Prompt Pack</Link>
        </Button>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-4xl px-6 pt-16 pb-14 text-center md:pt-24 md:pb-20">
        <p className="eyebrow">Powered by Aerchain agents</p>
        <h1 className="mt-5 text-balance text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl md:text-6xl">
          Messy vendor bids in.
          <br />
          <span className="text-gradient">Evidence-backed clarity</span> out.
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-ink/80">
          Bid Desk reads every vendor proposal, extracts each fact with a source snippet,
          flags what&rsquo;s missing or conflicting, and tells you who is actually
          comparable —{" "}
          <span className="font-serif text-xl italic text-brand">
            grounded, never invented.
          </span>
        </p>
        <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
          <Button asChild variant="gradient" size="lg">
            <Link href="/rfq">Enter workspace →</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/comparison">See a comparison</Link>
          </Button>
        </div>
      </section>

      {/* Pipeline */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {PIPELINE.map((step) => (
            <div
              key={step.n}
              className="card-hover rounded-2xl border border-border bg-card p-5"
            >
              <span className="grid size-9 place-items-center rounded-lg bg-secondary text-sm font-bold tabular-nums text-brand">
                {step.n}
              </span>
              <h3 className="mt-4 text-base font-bold">{step.title}</h3>
              <p className="mt-1.5 text-sm leading-snug text-muted-foreground">
                {step.blurb}
              </p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
