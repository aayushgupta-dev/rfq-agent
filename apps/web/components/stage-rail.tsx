"use client";
import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "RFQ Overview", href: "/rfq" },
  { label: "Vendor Input", href: "/input" },
  { label: "Extraction Review", href: "/extraction" },
  { label: "Comparison", href: "/comparison" },
  { label: "Prompt Trace", href: "/trace" },
] as const;

export function StageRail() {
  const pathname = usePathname();

  return (
    // ponytail: responsive via Tailwind only — hidden sm, icon-only md, full labels lg (D-26)
    <nav
      data-slot="stage-rail"
      className="hidden md:flex md:w-[60px] lg:w-64 shrink-0 flex-col bg-sidebar border-r border-sidebar-border"
    >
      {/* Co-brand: Aerchain wordmark + Bid Desk workspace label */}
      <Link
        href="/"
        className="flex flex-col gap-1.5 px-3 lg:px-5 py-5 border-b border-sidebar-border"
        aria-label="Bid Desk — an Aerchain workspace"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/aerchain-wordmark.png"
          alt="Aerchain"
          className="hidden lg:block h-4 w-auto"
        />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/aerchain-mark.svg"
          alt="Aerchain"
          className="lg:hidden h-6 w-6 mx-auto"
        />
        <span className="hidden lg:block eyebrow">Bid Desk · workspace</span>
      </Link>

      <div className="flex flex-col gap-1 p-2 lg:px-3 lg:py-4">
        <span className="hidden lg:block eyebrow px-2 pb-2">Pipeline</span>
        {NAV_ITEMS.map(({ label, href }, i) => {
          const isActive = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-2 lg:px-3 min-h-11 text-[13px] font-semibold transition-colors",
                isActive
                  ? "bg-secondary text-brand"
                  : "text-muted-foreground hover:bg-accent hover:text-brand",
              )}
              aria-current={isActive ? "page" : undefined}
            >
              {/* Numbered marker — the stages are a real pipeline sequence */}
              <span
                className={cn(
                  "grid place-items-center size-7 shrink-0 rounded-lg text-xs tabular-nums mx-auto lg:mx-0 transition-colors",
                  isActive
                    ? "bg-brand text-white"
                    : "bg-secondary text-brand/70 group-hover:bg-white",
                )}
              >
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="hidden lg:block truncate">{label}</span>
            </Link>
          );
        })}
      </div>

      <div className="mt-auto hidden lg:block px-5 py-4 border-t border-sidebar-border">
        <span className="eyebrow">Powered by Aerchain agents</span>
      </div>
    </nav>
  );
}
