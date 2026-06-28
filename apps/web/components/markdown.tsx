import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { cn } from "@/lib/utils";

// Grounded vendor text often carries markdown (## headings, **bold**, lists, tables).
// Render it instead of showing raw syntax. Headings are downscaled to body weight so a
// vendor's section heading inside a field value never blows up the row layout.
const components: Components = {
  h1: (p) => <p className="font-semibold" {...p} />,
  h2: (p) => <p className="font-semibold" {...p} />,
  h3: (p) => <p className="font-semibold" {...p} />,
  h4: (p) => <p className="font-semibold" {...p} />,
  p: (p) => <p className="mb-1.5 last:mb-0" {...p} />,
  ul: (p) => <ul className="list-disc pl-4 mb-1.5 space-y-0.5" {...p} />,
  ol: (p) => <ol className="list-decimal pl-4 mb-1.5 space-y-0.5" {...p} />,
  a: (p) => <a className="underline underline-offset-2" {...p} />,
  code: (p) => <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]" {...p} />,
  table: (p) => (
    <div className="overflow-x-auto">
      <table className="my-1.5 border-collapse text-left" {...p} />
    </div>
  ),
  th: (p) => <th className="border border-border px-2 py-1 font-semibold" {...p} />,
  td: (p) => <td className="border border-border px-2 py-1 align-top" {...p} />,
};

// ponytail: one renderer for every place grounded markdown is shown (field values,
// evidence, prompt pack). `prose`-style spacing handled by the components map above —
// no @tailwindcss/typography dependency needed.
export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div className={cn("[&_strong]:font-semibold", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
