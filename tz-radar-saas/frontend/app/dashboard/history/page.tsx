"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  History, Calendar, Database, AlertTriangle, Eye, Loader2, ArrowRight,
  TrendingUp, RefreshCw, BarChart2, CheckCircle2, XCircle
} from "lucide-react";
import { listReports, RadarReport } from "@/lib/api";

export default function HistoryPage() {
  const [reports, setReports] = useState<RadarReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clientId, setClientId] = useState("");

  useEffect(() => {
    let storedClientId = "";
    if (typeof window !== "undefined") {
      storedClientId = localStorage.getItem("radar_client_id") || "";
      setClientId(storedClientId);
    }
    fetchReports(storedClientId);
  }, []);

  const fetchReports = async (cid: string = "") => {
    setLoading(true);
    setError(null);
    try {
      const data = await listReports(cid);
      // Ensure we get list of reports
      const reportsList = data.reports || [];
      setReports(reportsList);
    } catch (err: any) {
      console.error("Failed to load reports history:", err);
      setError("Unable to connect to the backend server. Is the API running?");
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return "N/A";
    try {
      const date = new Date(dateStr);
      return date.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    } catch {
      return dateStr;
    }
  };

  // Aggregated Stats
  const completedScans = reports.filter(r => r.status === "COMPLETED");
  const totalPostsAnalyzed = completedScans.reduce((sum, r) => sum + (r.raw_post_count || 0), 0);
  const totalCrisisSignals = completedScans.reduce((sum, r) => sum + (r.crisisAlerts?.length || 0), 0);
  const averagePostsPerScan = completedScans.length > 0 ? Math.round(totalPostsAnalyzed / completedScans.length) : 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-900 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
            <History className="w-7 h-7 text-indigo-400" />
            Scan Archive & History
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Browse and load previous geopolitical scans and market summaries.
          </p>
        </div>
        <button
          onClick={() => fetchReports(clientId)}
          disabled={loading}
          className="bg-slate-900 hover:bg-slate-800 active:bg-slate-750 text-slate-100 px-4 py-2.5 rounded-xl border border-slate-800 font-medium transition-all flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-indigo-400" : ""}`} /> Reload Logs
        </button>
      </div>

      {/* Stats Summary Grid */}
      {!loading && !error && reports.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-900 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Scans Run</span>
              <Database className="w-5 h-5 text-indigo-400" />
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-2">{reports.length}</p>
          </div>
          
          <div className="bg-slate-900 border border-slate-900 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Posts Analyzed</span>
              <BarChart2 className="w-5 h-5 text-indigo-400" />
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-2">{totalPostsAnalyzed}</p>
          </div>

          <div className="bg-slate-900 border border-slate-900 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Posts / Scan</span>
              <TrendingUp className="w-5 h-5 text-indigo-400" />
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-2">{averagePostsPerScan}</p>
          </div>

          <div className="bg-slate-900 border border-slate-900 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-medium">Crisis Warnings</span>
              <AlertTriangle className="w-5 h-5 text-amber-500" />
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-2">{totalCrisisSignals}</p>
          </div>
        </div>
      )}

      {/* Main List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 space-y-4">
          <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
          <p className="text-slate-400 text-sm">Retrieving scan execution history...</p>
        </div>
      ) : error ? (
        <div className="text-center py-16 bg-slate-900/50 border border-rose-900/30 rounded-2xl max-w-xl mx-auto p-6 space-y-4">
          <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto" />
          <h3 className="text-lg font-semibold text-slate-200">Unable to Fetch Logs</h3>
          <p className="text-slate-400 text-sm leading-relaxed">{error}</p>
          <button 
            onClick={() => fetchReports(clientId)}
            className="px-5 py-2.5 bg-rose-950/30 border border-rose-900/50 text-rose-300 rounded-xl hover:bg-rose-900/30 transition-colors text-sm font-semibold"
          >
            Try Reconnecting
          </button>
        </div>
      ) : reports.length === 0 ? (
        <div className="text-center py-20 bg-slate-900 border border-slate-900 rounded-2xl">
          <History className="w-12 h-12 text-slate-700 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-300">No Logged Scans</h3>
          <p className="text-slate-500 text-sm mt-1 max-w-md mx-auto leading-relaxed">
            No intelligence scans have been executed yet or the API in-memory log has cleared. Run a scan from the main dashboard to seed history.
          </p>
          <Link 
            href="/dashboard" 
            className="mt-6 inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-xl text-sm transition-all"
          >
            Go to Dashboard <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-900 rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/40 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="px-6 py-4">Scan Date & Time</th>
                  <th className="px-6 py-4">Job / Report ID</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Analyzed Posts</th>
                  <th className="px-6 py-4 text-right">Crisis Warnings</th>
                  <th className="px-6 py-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {reports.map((report) => (
                  <tr key={report.id} className="hover:bg-slate-800/30 transition-colors group">
                    <td className="px-6 py-4.5 whitespace-nowrap text-sm font-medium text-slate-200">
                      <span className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                        {formatDateTime(report.reportDate)}
                      </span>
                    </td>
                    <td className="px-6 py-4.5 font-mono text-xs text-slate-400 whitespace-nowrap">
                      {report.id}
                    </td>
                    <td className="px-6 py-4.5 whitespace-nowrap">
                      {report.status === "COMPLETED" ? (
                        <span className="px-2.5 py-1 bg-emerald-950/40 text-emerald-400 border border-emerald-900/60 rounded-full text-xs font-semibold flex items-center w-fit gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Success
                        </span>
                      ) : report.status === "FAILED" ? (
                        <span className="px-2.5 py-1 bg-rose-950/40 text-rose-400 border border-rose-900/60 rounded-full text-xs font-semibold flex items-center w-fit gap-1">
                          <XCircle className="w-3.5 h-3.5" /> Failed
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 bg-indigo-950/40 text-indigo-400 border border-indigo-900/60 rounded-full text-xs font-semibold flex items-center w-fit gap-1">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Processing
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4.5 text-right font-mono text-sm font-semibold text-slate-300">
                      {report.raw_post_count || 0}
                    </td>
                    <td className="px-6 py-4.5 text-right font-mono text-sm font-semibold text-slate-300">
                      {report.crisisAlerts?.length || 0}
                    </td>
                    <td className="px-6 py-4.5 text-center whitespace-nowrap">
                      <Link
                        href={`/dashboard?jobId=${report.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-indigo-900/40 hover:bg-indigo-600 border border-indigo-800 text-indigo-300 hover:text-white rounded-lg transition-all"
                      >
                        <Eye className="w-3.5 h-3.5" /> Load Scan
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
