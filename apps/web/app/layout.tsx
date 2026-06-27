import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Bid Desk",
  description: "Prompt-driven procurement copilot — evidence-backed vendor comparison",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
