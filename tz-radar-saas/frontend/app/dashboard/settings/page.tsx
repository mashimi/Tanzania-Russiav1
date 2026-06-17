"use client";

import { useState, useEffect } from "react";
import { Settings, Save, CheckCircle2, ShieldAlert, Cpu, Database, Key, Server, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const [clientId, setClientId] = useState("demo-client");
  const [customKeywords, setCustomKeywords] = useState("");
  const [saved, setSaved] = useState(false);
  const [healthStatus, setHealthStatus] = useState<"checking" | "online" | "offline">("checking");
  const [backendVersion, setBackendVersion] = useState("Unknown");
  const [checkingHealth, setCheckingHealth] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedClientId = localStorage.getItem("radar_client_id");
      const storedKeywords = localStorage.getItem("radar_custom_keywords");
      
      if (storedClientId) setClientId(storedClientId);
      if (storedKeywords) {
        try {
          const parsed = JSON.parse(storedKeywords);
          if (Array.isArray(parsed)) {
            setCustomKeywords(parsed.join(", "));
          }
        } catch {
          setCustomKeywords(storedKeywords);
        }
      }
    }
    checkHealth();
  }, []);

  const checkHealth = async () => {
    setCheckingHealth(true);
    setHealthStatus("checking");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${apiUrl}/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        const data = await res.json();
        setHealthStatus("online");
        setBackendVersion(data.version || "2.0.0");
      } else {
        setHealthStatus("offline");
      }
    } catch {
      setHealthStatus("offline");
    } finally {
      setCheckingHealth(false);
    }
  };

  const handleSave = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("radar_client_id", clientId.trim());
      
      // Clean and split keywords
      const kwArray = customKeywords
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k.length > 0);
      
      localStorage.setItem("radar_custom_keywords", JSON.stringify(kwArray));
      
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-slate-900 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
            <Settings className="w-7 h-7 text-indigo-400" />
            Control Center & Settings
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Configure search parameters, metadata targets, and inspect environment health status.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Settings Form */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-slate-900 border border-slate-900 rounded-2xl p-6 space-y-6 shadow-xl">
            <h2 className="text-lg font-semibold flex items-center gap-2 text-slate-100 border-b border-slate-800 pb-3">
              <Cpu className="w-5 h-5 text-indigo-400" />
              Scanner Parameters
            </h2>

            {/* Client ID */}
            <div className="space-y-2">
              <label htmlFor="clientId" className="text-sm font-medium text-slate-300 block">
                Target Client ID
              </label>
              <input
                id="clientId"
                type="text"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                placeholder="e.g. demo-client"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-950/80 text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
              <p className="text-xs text-slate-500">
                Determines which scope client reports and configurations belong to on the backend store.
              </p>
            </div>

            {/* Custom Keywords */}
            <div className="space-y-2">
              <label htmlFor="keywords" className="text-sm font-medium text-slate-300 block">
                Custom Target Keywords (Comma separated)
              </label>
              <textarea
                id="keywords"
                value={customKeywords}
                onChange={(e) => setCustomKeywords(e.target.value)}
                placeholder="e.g. Zanzibar resort booking, Serengeti safari review, Tanzania direct flight"
                rows={4}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-950/80 text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
              <p className="text-xs text-slate-500">
                These keywords will be appended dynamically to the default market scanning matrix (China/Russia) when a new scan is executed.
              </p>
            </div>

            {/* Save Button */}
            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={handleSave}
                className="bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white px-5 py-2.5 rounded-xl font-medium transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/15"
              >
                <Save className="w-4.5 h-4.5" /> Save Configuration
              </button>
              {saved && (
                <span className="text-emerald-400 text-sm font-medium flex items-center gap-1.5 animate-in fade-in duration-200">
                  <CheckCircle2 className="w-4 h-4" /> Parameters updated locally!
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Status Panel */}
        <div className="space-y-6">
          {/* Health Check Card */}
          <div className="bg-slate-900 border border-slate-900 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h2 className="text-base font-semibold flex items-center gap-2 text-slate-100">
                <Server className="w-4.5 h-4.5 text-indigo-400" />
                Backend Status
              </h2>
              <button 
                onClick={checkHealth}
                disabled={checkingHealth}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
                title="Refresh Health"
              >
                <RefreshCw className={`w-4 h-4 ${checkingHealth ? "animate-spin text-indigo-400" : ""}`} />
              </button>
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-sm text-slate-400">Connection Status</span>
              {healthStatus === "online" ? (
                <span className="px-2.5 py-1 bg-emerald-950/40 text-emerald-400 border border-emerald-900/60 rounded-full text-xs font-semibold flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Online
                </span>
              ) : healthStatus === "offline" ? (
                <span className="px-2.5 py-1 bg-rose-950/40 text-rose-400 border border-rose-900/60 rounded-full text-xs font-semibold flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-rose-400" /> Offline
                </span>
              ) : (
                <span className="px-2.5 py-1 bg-slate-850/40 text-slate-400 border border-slate-800 rounded-full text-xs font-semibold flex items-center gap-1">
                  Checking...
                </span>
              )}
            </div>

            <div className="flex items-center justify-between py-1">
              <span className="text-sm text-slate-400">API Version</span>
              <span className="font-mono text-xs text-slate-300">{backendVersion}</span>
            </div>
            
            <div className="flex items-center justify-between py-1">
              <span className="text-sm text-slate-400">Port</span>
              <span className="font-mono text-xs text-slate-300">8000</span>
            </div>
          </div>

          {/* Integrations Health */}
          <div className="bg-slate-900 border border-slate-900 rounded-2xl p-6 shadow-xl space-y-4">
            <h2 className="text-base font-semibold flex items-center gap-2 text-slate-100 border-b border-slate-800 pb-3">
              <Database className="w-4.5 h-4.5 text-indigo-400" />
              Integrations Summary
            </h2>

            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-indigo-400" /> OpenAI Summary
                </span>
                <span className="text-xs font-medium text-emerald-400">Configured (GPT-4o)</span>
              </div>
              
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Server className="w-3.5 h-3.5 text-indigo-400" /> Exa MCP Search
                </span>
                <span className="text-xs font-medium text-emerald-400">Active</span>
              </div>

              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Server className="w-3.5 h-3.5 text-indigo-400" /> XHS Fetcher
                </span>
                <span className="text-xs font-medium text-emerald-400">Active</span>
              </div>
            </div>

            <div className="pt-2">
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 flex items-start gap-2.5">
                <ShieldAlert className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  The Exa search crawler utilizes deep retrieval via Jina AI. Search targets are managed through the dynamic keyword matrix.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
