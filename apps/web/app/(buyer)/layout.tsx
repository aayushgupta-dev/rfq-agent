import { BuyerProvider } from "@/contexts/BuyerContext";
import { StageRail } from "@/components/stage-rail";
import { Button } from "@/components/ui/button";

export default function BuyerLayout({ children }: { children: React.ReactNode }) {
  return (
    <BuyerProvider>
      <div className="flex min-h-screen">
        {/* Hamburger placeholder shown only on sm (<768px) */}
        <div className="md:hidden fixed top-4 left-4 z-50">
          <Button variant="ghost" size="icon" aria-label="Open menu">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </Button>
        </div>
        <StageRail />
        <main className="flex-1 min-w-0 overflow-y-auto">
          <div className="max-w-5xl mx-auto p-8">{children}</div>
        </main>
      </div>
    </BuyerProvider>
  );
}
