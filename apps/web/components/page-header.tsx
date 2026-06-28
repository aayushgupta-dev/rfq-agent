import * as React from "react";
import { cn } from "@/lib/utils";

// Shared screen header — eyebrow + heavy title + optional description and action slot.
// Keeps the five buyer screens visually consistent with the Aerchain design language.
export function PageHeader({
  eyebrow,
  title,
  description,
  action,
  className,
}: {
  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("mb-8", className)}>
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight leading-[1.1]">
            {title}
          </h1>
          {description ? (
            <p className="mt-2 max-w-2xl text-sm md:text-base leading-relaxed text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
    </header>
  );
}
