"use client";
import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { FileText, Upload, Search, BarChart2, GitBranch } from "lucide-react";

const NAV_ITEMS = [
  { label: "RFQ Overview", href: "/rfq", icon: FileText },
  { label: "Vendor Input", href: "/input", icon: Upload },
  { label: "Extraction Review", href: "/extraction", icon: Search },
  { label: "Comparison", href: "/comparison", icon: BarChart2 },
  { label: "Prompt Trace", href: "/trace", icon: GitBranch },
] as const;

export function StageRail() {
  const pathname = usePathname();

  return (
    // ponytail: responsive via Tailwind only — hidden sm, icon-only md, full labels lg (D-26)
    <nav
      data-slot="stage-rail"
      className="hidden md:flex md:w-[60px] lg:w-60 shrink-0 flex-col bg-card border-r border-border"
    >
      <div className="flex flex-col gap-1 p-2">
        {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-4 min-h-11 text-xs font-semibold rounded-md transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className="size-4 shrink-0" />
              {/* Label hidden on md (icon-only), shown on lg */}
              <span className="hidden lg:block truncate">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
