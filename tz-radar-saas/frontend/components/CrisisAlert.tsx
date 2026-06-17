"use client";

import { AlertTriangle, X } from "lucide-react";
import type { SocialPost } from "@/lib/api";

interface CrisisAlertProps {
  alerts: SocialPost[];
}

export default function CrisisAlert({ alerts }: CrisisAlertProps) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="bg-crisis-50 border-l-4 border-crisis-500 p-4 rounded-r-lg shadow-sm">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-6 h-6 text-crisis-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-crisis-900 text-base">
              ⚠️ Crisis Alerts Detected
            </h3>
            <span className="inline-flex items-center justify-center bg-crisis-100 text-crisis-700 text-xs font-bold px-2.5 py-0.5 rounded-full">
              {alerts.length} alert{alerts.length > 1 ? "s" : ""}
            </span>
          </div>
          <p className="text-crisis-700 text-sm mt-1.5 leading-relaxed">
            {alerts.length} potential reputation risk{alerts.length > 1 ? "s" : ""}{" "}
            found across monitored platforms.
          </p>
          <div className="mt-3 space-y-2">
            {alerts.slice(0, 3).map((alert, idx) => (
              <div
                key={idx}
                className="bg-white bg-opacity-70 rounded-lg p-3 border border-crisis-200 text-sm"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-crisis-600 uppercase tracking-wider">
                    [{alert.platform}]
                  </span>
                  <span className="text-xs text-slate-500">
                    @{alert.author}
                  </span>
                </div>
                <p className="text-slate-700 text-xs leading-relaxed">
                  {(alert.content_snippet || "").length > 150
                    ? (alert.content_snippet || "").slice(0, 150) + "..."
                    : alert.content_snippet || "No content available"}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}