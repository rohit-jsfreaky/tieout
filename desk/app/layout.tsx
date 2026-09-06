import type { Metadata } from "next";
import "@fontsource-variable/fraunces";
import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
import "./globals.css";

import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata: Metadata = {
  title: "Tieout — the AP exception desk",
  description:
    "An agent that only works the invoices that broke. It investigates, escalates once, learns the rule, and clears the next one itself.",
  applicationName: "Tieout",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <TooltipProvider>{children}</TooltipProvider>
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
}
