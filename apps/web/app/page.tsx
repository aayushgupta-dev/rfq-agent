// Shell page — renders nothing real yet (D-01).
// Imports FlagStatus from @aerchain/shared-types to prove the pnpm workspace link resolves.
// Plan 05 will replace this with the real buyer UI.
import type { FlagStatus } from "@aerchain/shared-types";

// Type annotation proves the link is wired — value is never rendered (shell only).
const _placeholderStatus: FlagStatus = "missing";

export default function Home() {
  return (
    <main>
      <p>Bid Desk — workspace link verified ({_placeholderStatus})</p>
    </main>
  );
}
