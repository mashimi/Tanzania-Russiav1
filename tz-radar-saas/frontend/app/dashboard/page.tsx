"use client";

import { useState, useCallback } from "react";
import {
  AlertTriangle,
  TrendingUp,
  ShieldCheck,
  RefreshCw,
  BarChart3,
  Users,
  Search,
  Clock,
} from "lucide-react";
import CrisisAlert from "@/components/CrisisAlert";
import MarketPulse from "@/components/MarketPulse";
import { triggerScan, getReport } from "@/lib/api";
import type { RadarReport } from "@/lib/api";

export default function DashboardPage() {
  const [report, setReport] = useState<RadarReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const handleScan = useCallback(async () => {
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      // 1. Trigger background scan
      const triggerRes = await triggerScan(
        "client-123",
        ["Four Seasons Zanzibar", "Serengeti luxury safari"]
      );
      setJobId(triggerRes.job_id);

      // 2. Poll for completion every 3 seconds
      const poll = setInterval(async () => {
        try {
          const statusRes = await getReport(triggerRes.job_id);
          if (
            statusRes.status === "COMPLETED" ||
            statusRes.status === "FAILED"
          ) {
            setReport(statusRes);
            setLoading(false);
            clearInterval(poll);
          }
        } catch {
          // Retry on network error
        }
      }, 3000);

      // Safety timeout: stop polling after 120 seconds
      setTimeout(() => {
        clearInterval(poll);
        if (loading) {
          setLoading(false);
          setError("Scan timed out. The backend may be unavailable.");
        }
      }, 120000);
    } catch (err: any) {
      setLoading(false);
      setError(err?.message || "Failed to trigger scan");
    }
  }, [loading]);

  // Compute stats for summary cards
  const totalPosts =
    (report?.chinaInsights?.reduce(
      (sum, i) => sum + (i.posts?.length || 0),
      0
    ) || 0) +
    (report?.russiaInsights?.reduce(
      (sum, i) => sum + (i.posts?.length || 0),
      0
    ) || 0);

  const alertCount = report?.crisisAlerts?.length || 0;
  const insightCount =
    (report?.chinaInsights?.length || 0) +
    (report?.russiaInsights?.length || 0);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* ── Header ── */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Geopolitical Tourism Radar
          </h1>
          <p className="text-slate-500 mt-1">
            Real-time intelligence for China & Russia markets — tracking the
            diplomatic dividend.
          </p>
        </div>
        <button
          onClick={handleScan}
          disabled={loading}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
        >
          <RefreshCw
            className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
          />
          {loading ? "Scanning Markets..." : "Run New Radar Scan"}
        </button>
      </div>

      {/* ── Loading State ── */}
      {loading && !report && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-center">
          <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
          <h3 className="font-semibold text-blue-900">Scan in Progress</h3>
          <p className="text-blue-700 text-sm mt-1">
            Scanning China & Russia markets for Tanzania-related
            conversations...
            {jobId && (
              <span className="block text-xs text-blue-500 mt-1">
                Job ID: {jobId.slice(0, 8)}...
              </span>
            )}
          </p>
        </div>
      )}

      {/* ── Error State ── */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* ── Empty State ── */}
      {!report && !loading && !error && (
        <div className="text-center py-20 bg-white rounded-xl border border-dashed border-slate-300 shadow-sm">
          <TrendingUp className="w-14 h-14 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900">
            No Recent Scans
          </h3>
          <p className="text-slate-500 mt-1 max-w-md mx-auto">
            Click <strong>"Run New Radar Scan"</strong> to fetch the
            latest market intelligence from China (XiaoHongShu) and Russia
            (travel forums & Exa).
          </p>
        </div>
      )}

      {/* ── Report View ── */}
      {report && report.status === "COMPLETED" && (
        <>
          {/* Summary Cards Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Search className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">
                    {totalPosts}
                  </p>
                  <p className="text-xs text-slate-500">Posts Collected</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                  <LightbulbIcon className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">
                    {insightCount}
                  </p>
                  <p className="text-xs text-slate-500">Insights Found</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-crisis-100 rounded-lg flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-crisis-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">
                    {alertCount}
                  </p>
                  <p className="text-xs text-slate-500">Crisis Alerts</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-900">
                    {report.reportDate
                      ? new Date(report.reportDate).toLocaleDateString()
                      : "Today"}
                  </p>
                  <p className="text-xs text-slate-500">Last Scan</p>
                </div>
              </div>
            </div>
          </div>

          {/* Crisis Alert Banner */}
          {alertCount > 0 && <CrisisAlert alerts={report.crisisAlerts} />}

          {/* Executive Summary */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-blue-600" />
                Executive Summary
              </h2>
            </div>
            <div className="px-6 py-4">
              <p className="text-slate-700 leading-relaxed">
                {report.executiveSummary}
              </p>
            </div>
          </div>

          {/* Market Pulse (China/Russia Tabs) */}
          <MarketPulse
            chinaInsights={report.chinaInsights}
            russiaInsights={report.russiaInsights}
          />
        </>
      )}

      {/* ── Failed State ── */}
      {report && report.status === "FAILED" && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <h3 className="font-semibold text-red-900">Scan Failed</h3>
          <p className="text-red-700 text-sm mt-1">
            {report.executiveSummary}
          </p>
          <button
            onClick={handleScan}
            className="mt-4 inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Retry Scan
          </button>
        </div>
      )}
    </div>
  );
}

// Inline icon component to avoid extra import (lucide doesn't have LightbulbIcon)
function LightbulbIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
      />
    </svg>
  );
}