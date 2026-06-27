// Shell page — UI-substrate proof (01-05).
// - FlagStatus import proves the pnpm workspace link resolves (01-01 proof, preserved).
// - The shadcn <Button> proves the Tailwind v4 + shadcn substrate flows end-to-end.
// Phase 5 will replace this with the real buyer UI.
import type { FlagStatus } from "@aerchain/shared-types";
import { Button } from "@/components/ui/button";

// Type annotation proves the link is wired — value is never rendered (shell only).
const _placeholderStatus: FlagStatus = "missing";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4">
      <p>Bid Desk — workspace link verified ({_placeholderStatus})</p>
      <Button>Bid Desk</Button>
    </main>
  );
}
