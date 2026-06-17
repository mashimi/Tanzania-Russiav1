"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, History, Settings, Radar, Activity } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  // Helper to determine if a link is active.
  // /dashboard matches exactly. /dashboard/history matches history. /dashboard/settings matches settings.
  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/dashboard" || pathname === "/dashboard/";
    }
    return pathname.startsWith(href);
  };

  const getLinkClass = (href: string) => {
    const base = "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150";
    if (isActive(href)) {
      return `${base} bg-indigo-600 text-white shadow-sm shadow-indigo-500/10`;
    }
    return `${base} text-slate-400 hover:text-slate-200 hover:bg-slate-800/60`;
  };

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 text-slate-300 flex flex-col flex-shrink-0 h-screen select-none">
      {/* Logo Section */}
      <div className="px-6 py-5 border-b border-slate-900">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-500/20">
            TZ
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-100 tracking-tight flex items-center gap-1.5">
              Tourism Radar
            </h1>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
              Geopolitical Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1.5">
        <Link href="/dashboard" className={getLinkClass("/dashboard")}>
          <LayoutDashboard className="w-4.5 h-4.5" />
          <span>Dashboard</span>
        </Link>
        
        <Link href="/dashboard/intelligence-feed" className={getLinkClass("/dashboard/intelligence-feed")}>
          <Activity className="w-4.5 h-4.5" />
          <span>Intelligence Feed</span>
        </Link>
        
        <Link href="/dashboard/history" className={getLinkClass("/dashboard/history")}>
          <History className="w-4.5 h-4.5" />
          <span>Scan History</span>
        </Link>
        
        <Link href="/dashboard/settings" className={getLinkClass("/dashboard/settings")}>
          <Settings className="w-4.5 h-4.5" />
          <span>Settings</span>
        </Link>
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-slate-900 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span className="text-[10px] text-slate-500 font-medium tracking-wide uppercase">
          Agent Reach Active
        </span>
      </div>
    </aside>
  );
}
