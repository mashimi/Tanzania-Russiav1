"use client";

import { useState, useEffect } from "react";
import { 
  AlertTriangle, TrendingUp, ShieldCheck, Activity, 
  Globe, Briefcase, Loader2, RefreshCw, CheckCircle2, XCircle 
} from "lucide-react";

// --- Types ---
interface SocialPost {
  platform: string;
  author: string;
  content_snippet: string;
  engagement: number;
  is_crisis: boolean;
}

interface MarketInsight {
  trend: string;
  sentiment: string;
  action: string;
  posts: SocialPost[];
}

interface RadarReport {
  id: string;
  clientId: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  executiveSummary: string;
  chinaInsights: MarketInsight[];
  russiaInsights: MarketInsight[];
  crisisAlerts: SocialPost[];
  reportDate: string | null;
  raw_post_count: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DashboardPage() {
  const [report, setReport] = useState<RadarReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const runScan = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    
    try {
      // 1. Trigger the scan
      const triggerRes = await fetch(`${API_URL}/api/v1/radar/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: "demo-client", custom_keywords: [] }),
      });
      
      if (!triggerRes.ok) throw new Error("Failed to trigger scan");
      
      const { job_id } = await triggerRes.json();
      setJobId(job_id);

      // 2. Poll for results
      const poll = setInterval(async () => {
        try {
          const res = await fetch(`${API_URL}/api/v1/radar/${job_id}`);
          if (!res.ok) throw new Error("Failed to fetch report");
          
          const data: RadarReport = await res.json();
          
          if (data.status === "COMPLETED") {
            setReport(data);
            setLoading(false);
            clearInterval(poll);
          } else if (data.status === "FAILED") {
            setError(data.executiveSummary || "Scan failed. Please check backend logs.");
            setLoading(false);
            clearInterval(poll);
          }
          // If PROCESSING, the interval continues
        } catch (err) {
          setError("Network error while polling. Is the backend running?");
          setLoading(false);
          clearInterval(poll);
        }
      }, 3000); // Poll every 3 seconds

    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
      setLoading(false);
    }
  };

  // Render States
  if (loading) return <SkeletonDashboard />;
  if (error) return <ErrorState message={error} onRetry={runScan} />;
  if (!report) return <EmptyState onScan={runScan} />;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 p-6 space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
            <Globe className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Geopolitical Tourism Radar
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1.5">
            Real-time market intelligence for China & Russia • Last updated:{" "}
            {report.reportDate ? new Date(report.reportDate).toLocaleString() : "N/A"}
          </p>
        </div>
        <button 
          onClick={runScan}
          className="bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white px-5 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 shadow-sm hover:shadow-md"
        >
          <RefreshCw className="w-4 h-4" /> Run New Scan
        </button>
      </div>

      {/* Crisis Alert Banner */}
      {report.crisisAlerts.length > 0 && (
        <div className="bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-xl p-5 flex items-start gap-4 animate-in fade-in slide-in-from-top-2">
          <div className="bg-rose-100 dark:bg-rose-900/50 p-2 rounded-full">
            <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-rose-700 dark:text-rose-300 text-base">
              Crisis Signals Detected
            </h3>
            <p className="text-sm text-rose-600/80 dark:text-rose-400/80 mt-1">
              {report.crisisAlerts.length} high-priority alert(s) require immediate attention. Review the details below.
            </p>
          </div>
        </div>
      )}

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard 
          title="Posts Analyzed" 
          value={report.raw_post_count.toLocaleString()} 
          icon={Globe} 
          color="blue" 
        />
        <KPICard 
          title="Crisis Alerts" 
          value={report.crisisAlerts.length.toString()} 
          icon={AlertTriangle} 
          color="rose" 
        />
        <KPICard 
          title="China Insights" 
          value={report.chinaInsights.length.toString()} 
          icon={TrendingUp} 
          color="emerald" 
        />
        <KPICard 
          title="Russia Insights" 
          value={report.russiaInsights.length.toString()} 
          icon={ShieldCheck} 
          color="indigo" 
        />
      </div>

      {/* Executive Summary */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-800 dark:text-slate-100">
          <Briefcase className="w-5 h-5 text-indigo-500" /> Executive Summary
        </h2>
        <div className="prose prose-slate dark:prose-invert max-w-none">
          <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-sm sm:text-base whitespace-pre-wrap">
            {report.executiveSummary || "No summary available for this scan."}
          </p>
        </div>
      </div>

      {/* Market Insights Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MarketSection title="China Market" data={report.chinaInsights} icon={TrendingUp} color="emerald" />
        <MarketSection title="Russia Market" data={report.russiaInsights} icon={ShieldCheck} color="indigo" />
      </div>
    </div>
  );
}

// --- Sub-components for clean, modular code ---

function KPICard({ title, value, icon: Icon, color }: { title: string, value: string, icon: any, color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400 border-blue-100 dark:border-blue-900",
    rose: "bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 border-rose-100 dark:border-rose-900",
    emerald: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-100 dark:border-emerald-900",
    indigo: "bg-indigo-50 text-indigo-600 dark:bg-indigo-950/40 dark:text-indigo-400 border-indigo-100 dark:border-indigo-900",
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex items-center gap-4 transition-transform hover:-translate-y-0.5">
      <div className={`p-3 rounded-lg border ${colors[color]}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-slate-50 mt-0.5">{value}</p>
      </div>
    </div>
  );
}

function MarketSection({ title, data, icon: Icon, color }: { title: string, data: MarketInsight[], icon: any, color: string }) {
  const borderColor = color === "emerald" ? "border-emerald-500" : "border-indigo-500";
  const badgeColor = color === "emerald" 
    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400"
    : "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-400";

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm flex flex-col h-full">
      <h2 className="text-lg font-semibold mb-5 flex items-center gap-2 text-slate-800 dark:text-slate-100">
        <Icon className={`w-5 h-5 text-${color}-500`} /> {title}
      </h2>
      
      {data && data.length > 0 ? (
        <div className="space-y-5 flex-1">
          {data.map((insight, idx) => (
            <div key={idx} className={`border-l-2 ${borderColor} pl-4 py-1`}>
              <p className="font-semibold text-slate-800 dark:text-slate-200 text-sm">{insight.trend}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1.5 leading-relaxed">{insight.action}</p>
              
              <div className="flex items-center gap-3 mt-3">
                <span className={`inline-block text-xs px-2.5 py-1 rounded-full font-medium ${badgeColor}`}>
                  {insight.sentiment}
                </span>
                {insight.posts.length > 0 && (
                  <span className="text-xs text-slate-400 dark:text-slate-500">
                    {insight.posts.length} source{insight.posts.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-center py-8 text-slate-400 dark:text-slate-500">
          <Activity className="w-8 h-8 mb-2 opacity-50" />
          <p className="text-sm">No specific insights detected for this market yet.</p>
        </div>
      )}
    </div>
  );
}

function SkeletonDashboard() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 space-y-8 max-w-7xl mx-auto animate-pulse">
      <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-6">
        <div className="space-y-2">
          <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-64"></div>
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-96"></div>
        </div>
        <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded-lg w-32"></div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-24 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        ))}
      </div>
      
      <div className="h-40 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-80 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        <div className="h-80 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
      </div>
    </div>
  );
}

function EmptyState({ onScan }: { onScan: () => void }) {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center p-6 max-w-2xl mx-auto">
      <div className="bg-indigo-50 dark:bg-indigo-950/30 p-5 rounded-2xl mb-6 ring-1 ring-indigo-100 dark:ring-indigo-900">
        <Globe className="w-12 h-12 text-indigo-600 dark:text-indigo-400" />
      </div>
      <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-50 mb-3">No Scan Data Available</h2>
      <p className="text-slate-500 dark:text-slate-400 mb-8 leading-relaxed">
        Start your first geopolitical intelligence scan to monitor real-time sentiment, crisis signals, and investment trends across Chinese and Russian markets.
      </p>
      <button 
        onClick={onScan}
        className="bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white px-8 py-3.5 rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg hover:shadow-xl hover:-translate-y-0.5"
      >
        <Activity className="w-5 h-5" /> Initialize Radar Scan
      </button>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string, onRetry: () => void }) {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center p-6 max-w-lg mx-auto">
      <div className="bg-rose-50 dark:bg-rose-950/30 p-5 rounded-full mb-6 ring-1 ring-rose-100 dark:ring-rose-900">
        <XCircle className="w-12 h-12 text-rose-500" />
      </div>
      <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-50 mb-3">Scan Failed</h2>
      <p className="text-slate-500 dark:text-slate-400 mb-8 leading-relaxed bg-rose-50 dark:bg-rose-950/20 p-4 rounded-lg border border-rose-100 dark:border-rose-900/50 text-sm">
        {message}
      </p>
      <button 
        onClick={onRetry}
        className="bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 px-6 py-3 rounded-lg font-medium transition-colors hover:bg-slate-800 dark:hover:bg-slate-200 flex items-center gap-2"
      >
        <RefreshCw className="w-4 h-4" /> Try Again
      </button>
    </div>
  );
}