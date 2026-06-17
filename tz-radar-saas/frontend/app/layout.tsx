import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "TZ Tourism Radar — Geopolitical Intelligence Dashboard",
  description:
    "Real-time monitoring of China and Russia market sentiment for Tanzanian tourism. Track diplomatic tailwinds from Head-of-State economic missions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-50 dark:bg-slate-950 min-h-screen antialiased text-slate-900 dark:text-slate-50">
        <div className="flex h-screen overflow-hidden">
          {/* Client Sidebar */}
          <Sidebar />

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}