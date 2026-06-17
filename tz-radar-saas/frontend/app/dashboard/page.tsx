"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { 
  AlertTriangle, TrendingUp, TrendingDown, Minus,
  ExternalLink, Flag, Archive, Search, Filter,
  MessageSquare, Eye, Heart, Share2, RefreshCw,
  CheckCircle2, XCircle, Globe, Briefcase, Loader2,
  ShieldCheck, Activity, Download, Calendar, Radar,
  Database, UserCheck
} from "lucide-react";

import TrendChart from "@/components/TrendChart";
import ReadinessGauge from "@/components/ReadinessGauge";
import MarketPulse from "@/components/MarketPulse";
import CrisisAlert from "@/components/CrisisAlert";
import { triggerScan, getReport, listReports, RadarReport, SocialPost, MarketInsight } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const paramJobId = searchParams.get("jobId");

  const [report, setReport] = useState<RadarReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStage, setProgressStage] = useState("");
  
  // Custom Settings (loaded from localStorage or default)
  const [clientId, setClientId] = useState("demo-client");
  const [customKeywords, setCustomKeywords] = useState<string[]>([]);
  
  // Filter & Search State
  const [timeRange, setTimeRange] = useState("24h");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("all");
  const [showTranslation, setShowTranslation] = useState(true);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [minEngagement, setMinEngagement] = useState(0);
  const [showCrisisOnly, setShowCrisisOnly] = useState(false);
  const [showInfluencersOnly, setShowInfluencersOnly] = useState(false);
  
  // Notification Toast State
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Load configuration and initial scan on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedClientId = localStorage.getItem("radar_client_id") || "demo-client";
      const storedKeywords = localStorage.getItem("radar_custom_keywords");
      
      setClientId(storedClientId);
      if (storedKeywords) {
        try {
          setCustomKeywords(JSON.parse(storedKeywords));
        } catch {
          setCustomKeywords([]);
        }
      }
    }
  }, []);

  // Fetch report when paramJobId changes or on initial mount
  useEffect(() => {
    const initialize = async () => {
      setLoading(true);
      setError(null);

      // If a jobId is specified in query string, fetch it
      if (paramJobId) {
        try {
          const fetched = await getReport(paramJobId);
          setReport(fetched);
          setJobId(paramJobId);
        } catch (err) {
          console.error("Error loading scan by query parameter:", err);
          setError("Requested scan report could not be found.");
        } finally {
          setLoading(false);
        }
      } else {
        // Auto-load latest completed scan for this client
        const storedClientId = localStorage.getItem("radar_client_id") || "demo-client";
        try {
          const listRes = await listReports(storedClientId);
          const completed = (listRes.reports || []).filter(r => r.status === "COMPLETED");
          
          if (completed.length > 0) {
            setReport(completed[0]);
            setJobId(completed[0].id);
          } else {
            // No previous scans
            setReport(null);
          }
        } catch (err) {
          console.error("Error loading latest scan:", err);
          // Don't set error blocker, just show empty state
        } finally {
          setLoading(false);
        }
      }
    };

    initialize();
  }, [paramJobId]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleRunScan = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    setProgressPercent(0);
    setProgressStage("Initializing scan pipeline...");
    
    try {
      const triggerRes = await triggerScan(clientId, customKeywords);
      setJobId(triggerRes.job_id);

      const poll = setInterval(async () => {
        try {
          const res = await fetch(`${API_URL}/api/v1/radar/${triggerRes.job_id}`);
          if (!res.ok) throw new Error("Failed to fetch report");
          
          const data = await res.json();
          
          if (data.progress_percent !== undefined) {
            setProgressPercent(data.progress_percent);
          }
          if (data.progress_stage) {
            setProgressStage(data.progress_stage);
          }
          
          if (data.status === "COMPLETED") {
            setReport(data);
            setProgressPercent(100);
            setProgressStage("Scan complete!");
            setLoading(false);
            clearInterval(poll);
            // Update URL with active report ID
            router.push(`/dashboard?jobId=${triggerRes.job_id}`);
            showToast("Scan finished successfully!");
          } else if (data.status === "FAILED") {
            setError(data.executiveSummary || "Scan failed. Please check backend logs.");
            setLoading(false);
            clearInterval(poll);
          }
        } catch (err) {
          setError("Network error while polling. Is the backend running?");
          setLoading(false);
          clearInterval(poll);
        }
      }, 3000);

    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
      setLoading(false);
    }
  };

  const handlePostAction = async (action: string, post: SocialPost) => {
    try {
      await fetch(`${API_URL}/api/v1/posts/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_url: post.url || "",
          action_type: action,
          platform: post.platform,
        }),
      });
      
      showToast(`Action '${action}' tracked successfully.`);

      // Update local state to show action taken
      if (report) {
        const updatedReport = { ...report };
        const updatePostInInsights = (insights: any[]) => {
          insights.forEach(insight => {
            const postIndex = (insight.posts || []).findIndex((p: any) => p.url === post.url);
            if (postIndex !== -1) {
              insight.posts[postIndex].action_taken = action;
              if (action === 'flag') insight.posts[postIndex].flagged = true;
              if (action === 'archive') insight.posts[postIndex].archived = true;
            }
          });
        };
        updatePostInInsights(updatedReport.chinaInsights);
        updatePostInInsights(updatedReport.russiaInsights);
        setReport(updatedReport);
      }
    } catch (err) {
      console.error(`Failed to execute action ${action}:`, err);
      showToast("Error tracking post action.");
    }
  };

  const exportReportData = () => {
    if (!report) return;
    const jsonStr = JSON.stringify(report, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `tz-radar-scan-${report.id.substring(0, 8)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast("Report exported successfully!");
  };

  // Filter posts based on criteria
  const filterPosts = (posts: any[]) => {
    return posts.filter(post => {
      if (showCrisisOnly && !post.is_crisis) return false;
      if (showInfluencersOnly && !post.is_influencer) return false;
      if (post.engagement < minEngagement) return false;
      if (selectedPlatform !== "all" && !post.platform.toLowerCase().includes(selectedPlatform.toLowerCase())) return false;
      if (selectedTopics.length > 0 && !post.topics.some((t: string) => selectedTopics.includes(t))) return false;
      if (searchQuery) {
        const searchLower = searchQuery.toLowerCase();
        const content = showTranslation && post.content_translated ? post.content_translated : post.content_original;
        if (!content.toLowerCase().includes(searchLower) && 
            !post.author.toLowerCase().includes(searchLower) &&
            !((post.topics || []).some((t: string) => t.toLowerCase().includes(searchLower)))) {
          return false;
        }
      }
      return true;
    });
  };

  if (loading) return <RadarLoading progressPercent={progressPercent} progressStage={progressStage} />;
  if (error) return <ErrorState message={error} onRetry={handleRunScan} />;
  if (!report) return <EmptyState onScan={handleRunScan} clientId={clientId} />;

  // Flatten posts across insights for feed display
  const allPosts: any[] = [
    ...(report.chinaInsights || []).flatMap((i: any) => i.posts || []),
    ...(report.russiaInsights || []).flatMap((i: any) => i.posts || []),
  ];

  const filteredPosts = filterPosts(allPosts);

  // Generate mock gauge and chart metrics aligned with the report stats
  const crisisCount = report.crisisAlerts?.length || 0;
  const readinessScore = Math.max(10, Math.min(100, 95 - crisisCount * 8));

  // Generate 7-day mentions trend data leading up to the scan date
  const generateTrendData = () => {
    const baseDate = report.reportDate ? new Date(report.reportDate) : new Date();
    const trendDataPoints = [];
    const totalPosts = report.raw_post_count || 50;
    
    for (let i = 6; i >= 0; i--) {
      const d = new Date(baseDate);
      d.setDate(baseDate.getDate() - i);
      const dateLabel = d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
      
      // Calculate realistic mentions & sentiment variation
      const randomSeed = Math.sin(i * 1.5) * 10;
      const mentions = Math.max(5, Math.round((totalPosts / 7) + randomSeed + (Math.random() * 6)));
      const sentiment = Math.max(20, Math.min(100, readinessScore + (Math.sin(i) * 5) + (Math.random() * 4)));
      
      trendDataPoints.push({
        date: dateLabel,
        mentions,
        sentiment: Math.round(sentiment),
      });
    }
    return trendDataPoints;
  };

  const trendData = generateTrendData();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6 max-w-7xl mx-auto relative">
      
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 border border-slate-800 text-slate-100 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2 animate-in fade-in slide-in-from-bottom-5 duration-200">
          <CheckCircle2 className="w-5 h-5 text-indigo-400" />
          <span className="text-sm font-semibold">{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-900 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Globe className="w-7 h-7 text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight">Geopolitical Tourism Radar</h1>
            <span className="px-2 py-0.5 bg-indigo-950 border border-indigo-900/40 text-indigo-400 text-xs rounded-full font-medium flex items-center gap-1.5 ml-2">
              <UserCheck className="w-3.5 h-3.5" /> Scope: {clientId}
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1.5">
            Real-time market intelligence for China & Russia • Last updated:{" "}
            {report.reportDate ? new Date(report.reportDate).toLocaleString() : "N/A"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={exportReportData}
            className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 active:bg-slate-750 text-slate-100 rounded-xl border border-slate-800 font-medium transition-all flex items-center gap-2 text-sm"
            title="Export Report to JSON"
          >
            <Download className="w-4 h-4" /> Export Report
          </button>
          <button 
            onClick={handleRunScan}
            className="bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white px-5 py-2.5 rounded-xl font-medium transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20 text-sm"
          >
            <RefreshCw className="w-4 h-4" /> Run New Scan
          </button>
        </div>
      </div>

      {/* Row 1: Crisis Banner if Alerts exist */}
      {report.crisisAlerts && report.crisisAlerts.length > 0 && (
        <CrisisAlert alerts={report.crisisAlerts} />
      )}

      {/* Row 2: Charts & Gauges Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {/* Trend Chart (Mentions & Sentiment over 7 days) */}
          <TrendChart data={trendData} />
        </div>
        <div>
          {/* Market Readiness score circle gauge */}
          <ReadinessGauge score={readinessScore} />
        </div>
      </div>

      {/* Row 3: Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Posts Analyzed" value={(report.raw_post_count || 0).toString()} icon={Globe} color="blue" />
        <KPICard title="Crisis Warnings" value={crisisCount.toString()} icon={AlertTriangle} color="rose" />
        <KPICard title="China Insights" value={(report.chinaInsights || []).length.toString()} icon={TrendingUp} color="emerald" />
        <KPICard title="Russia Insights" value={(report.russiaInsights || []).length.toString()} icon={ShieldCheck} color="indigo" />
      </div>

      {/* Row 4: Executive Summary */}
      <div className="bg-slate-900 border border-slate-900 rounded-2xl p-6 shadow-xl space-y-3">
        <h2 className="text-lg font-semibold flex items-center gap-2 text-slate-100">
          <Briefcase className="w-5 h-5 text-indigo-400" /> Executive AI Summary
        </h2>
        <div className="prose prose-invert max-w-none">
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base whitespace-pre-wrap">
            {report.executiveSummary || "No summary available for this scan."}
          </p>
        </div>
      </div>

      {/* Row 5: Feed & Recommendations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Intelligence Feed */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold flex items-center gap-2 text-slate-100">
            <Activity className="w-5 h-5 text-indigo-400" />
            Intelligence Feed
          </h2>

          {/* Filter Bar */}
          <div className="bg-slate-900 border border-slate-900 rounded-2xl p-4 space-y-4 shadow-xl">
            <div className="flex flex-wrap gap-3">
              <div className="flex-1 min-w-[250px] relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search posts, authors, topics..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-800 bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              
              <select 
                className="px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-950 text-slate-300 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
              >
                <option value="24h">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
              </select>
              
              <select
                className="px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-950 text-slate-300 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
                value={selectedPlatform}
                onChange={(e) => setSelectedPlatform(e.target.value)}
              >
                <option value="all">All Platforms</option>
                <option value="xiaohongshu">XiaoHongShu</option>
                <option value="exa (cn)">Exa (China)</option>
                <option value="exa (ru)">Exa (Russia)</option>
              </select>
              
              <button
                onClick={() => setShowTranslation(!showTranslation)}
                className={`px-4 py-2 rounded-xl font-medium text-xs transition-colors ${showTranslation ? 'bg-indigo-600 text-white shadow-sm' : 'bg-slate-800 text-slate-400'}`}
              >
                {showTranslation ? 'English Translation' : 'Original Language'}
              </button>
            </div>
            
            <div className="flex flex-wrap gap-4 items-center border-t border-slate-800/60 pt-3">
              <label className="flex items-center gap-2 text-sm select-none cursor-pointer">
                <input
                  type="checkbox"
                  checked={showCrisisOnly}
                  onChange={(e) => setShowCrisisOnly(e.target.checked)}
                  className="rounded border-slate-800 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-slate-300 text-xs">Crisis only</span>
              </label>
              
              <label className="flex items-center gap-2 text-sm select-none cursor-pointer">
                <input
                  type="checkbox"
                  checked={showInfluencersOnly}
                  onChange={(e) => setShowInfluencersOnly(e.target.checked)}
                  className="rounded border-slate-800 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-slate-300 text-xs">Influencers only</span>
              </label>
              
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Min engagement:</span>
                <input
                  type="number"
                  value={minEngagement}
                  onChange={(e) => setMinEngagement(Number(e.target.value))}
                  className="w-20 px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-200 text-xs focus:outline-none"
                  placeholder="0"
                />
              </div>
              
              <div className="flex items-center gap-2 ml-auto">
                <span className="text-xs text-slate-500">
                  Showing {filteredPosts.length} of {allPosts.length} posts
                </span>
              </div>
            </div>
          </div>

          {/* Posts list */}
          {filteredPosts.length > 0 ? (
            <div className="space-y-4">
              {filteredPosts.map((post, idx) => (
                <IntelligencePostCard 
                  key={`${post.url}-${idx}`} 
                  post={post} 
                  showTranslation={showTranslation}
                  onAction={handlePostAction}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-16 bg-slate-900 border border-slate-900 rounded-2xl">
              <Search className="w-12 h-12 text-slate-700 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No intelligence reports match your filters</p>
              <button 
                onClick={() => {
                  setSearchQuery("");
                  setShowCrisisOnly(false);
                  setShowInfluencersOnly(false);
                  setMinEngagement(0);
                  setSelectedPlatform("all");
                }}
                className="mt-3 text-indigo-400 hover:text-indigo-300 text-sm font-semibold"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>

        {/* MarketPulse Recommendations (Tabs side panel) */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold flex items-center gap-2 text-slate-100">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            Insights & Actions
          </h2>
          <MarketPulse chinaInsights={report.chinaInsights || []} russiaInsights={report.russiaInsights || []} />
        </div>
      </div>
    </div>
  );
}

// Wrap with Suspense to handle Next.js client searchParams correctly
export default function IntelligenceDashboard() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-slate-400 text-sm mt-3">Loading dashboard framework...</p>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}

// --- Sub-components ---

function KPICard({ title, value, icon: Icon, color }: { title: string, value: string, icon: any, color: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-950/30 text-blue-400 border-blue-900/60 shadow-blue-950/5",
    rose: "bg-rose-950/30 text-rose-400 border-rose-900/60 shadow-rose-950/5",
    emerald: "bg-emerald-950/30 text-emerald-400 border-emerald-900/60 shadow-emerald-950/5",
    indigo: "bg-indigo-950/30 text-indigo-400 border-indigo-900/60 shadow-indigo-950/5",
  };

  return (
    <div className="bg-slate-900 border border-slate-900 rounded-2xl p-5 shadow-xl flex items-center gap-4 transition-all duration-200 hover:translate-y-[-2px] hover:border-slate-800 select-none">
      <div className={`p-3 rounded-xl border ${colors[color]}`}>
        <Icon className="w-5.5 h-5.5" />
      </div>
      <div>
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
        <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
      </div>
    </div>
  );
}

function IntelligencePostCard({ post, showTranslation, onAction }: { post: any, showTranslation: boolean, onAction: (action: string, post: any) => void }) {
  const trend = post.trend_percentage;
  const content = showTranslation && post.content_translated ? post.content_translated : post.content_original;
  
  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-900 p-5 hover:border-slate-800 transition-all duration-200 shadow-lg">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <PlatformIcon platform={post.platform} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-200">{post.author}</span>
              {post.is_influencer && (
                <span className="px-2 py-0.5 bg-amber-950/40 border border-amber-900/50 text-amber-400 text-xs rounded-full font-medium flex items-center gap-1">
                  ⭐ {post.author_followers ? post.author_followers.toLocaleString() : "10K+"} followers
                </span>
              )}
              {post.is_crisis && (
                <span className="px-2 py-0.5 bg-rose-950/40 border border-rose-900/50 text-rose-455 text-xs rounded-full font-medium">
                  🚨 Warning
                </span>
              )}
            </div>
            <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
              <span className="font-medium text-slate-400">{post.platform}</span>
              <span>•</span>
              <span>{post.published_at ? new Date(post.published_at).toLocaleString() : 'Unknown date'}</span>
              {post.language && <span>• {post.language.toUpperCase()}</span>}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {post.screenshot_url && (
            <a 
              href={post.screenshot_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded-lg transition-colors"
              title="View screenshot"
            >
              <Eye className="w-4.5 h-4.5" />
            </a>
          )}
          <a 
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded-lg transition-colors"
            title="View original post"
          >
            <ExternalLink className="w-4.5 h-4.5" />
          </a>
        </div>
      </div>

      {/* Content */}
      <div className="mb-4">
        <p className="text-slate-300 leading-relaxed text-sm whitespace-pre-wrap">
          {content}
        </p>
        {showTranslation && post.content_translated && post.content_original !== post.content_translated && (
          <div className="mt-3 p-3 bg-slate-950/80 rounded-xl border border-slate-900">
            <p className="text-[10px] text-slate-550 mb-1 font-semibold uppercase tracking-wider">Original:</p>
            <p className="text-xs text-slate-400 whitespace-pre-wrap font-medium">{post.content_original}</p>
          </div>
        )}
      </div>

      {/* Engagement Metrics */}
      <div className="flex items-center gap-6 mb-4">
        <div className="flex items-center gap-2 text-slate-400">
          <Heart className="w-4 h-4 text-slate-500" />
          <span className="text-xs font-semibold">{post.engagement_details?.likes ? post.engagement_details.likes.toLocaleString() : (post.engagement || 0).toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <MessageSquare className="w-4 h-4 text-slate-500" />
          <span className="text-xs font-semibold">{post.engagement_details?.comments ? post.engagement_details.comments.toLocaleString() : 0}</span>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <Share2 className="w-4 h-4 text-slate-500" />
          <span className="text-xs font-semibold">{post.engagement_details?.shares ? post.engagement_details.shares.toLocaleString() : 0}</span>
        </div>
        
        {/* Trend Indicator */}
        {trend && trend !== 0 && (
          <div className={`flex items-center gap-1 ml-auto ${trend > 0 ? 'text-emerald-400' : 'text-rose-455'}`}>
            {trend > 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
            <span className="text-xs font-bold">{Math.abs(trend)}%</span>
          </div>
        )}
      </div>

      {/* Topics & Action tags */}
      <div className="flex items-center gap-1.5 mb-4 flex-wrap select-none">
        {(post.topics || []).map((topic: string) => (
          <span key={topic} className="px-2 py-1 bg-slate-950 border border-slate-800/80 text-slate-400 text-[10px] rounded-md font-medium">
            #{topic}
          </span>
        ))}
        {post.action_taken && (
          <span className="ml-auto px-2 py-1 bg-indigo-950 border border-indigo-900/60 text-indigo-400 text-[10px] rounded-md font-semibold flex items-center gap-1 animate-in fade-in duration-200">
            <CheckCircle2 className="w-3.5 h-3.5" /> {post.action_taken}
          </span>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-3 border-t border-slate-800/40">
        <button 
          onClick={() => onAction('respond', post)}
          disabled={post.action_taken === 'respond'}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-800 disabled:text-slate-550 text-white rounded-xl transition-colors shadow-md shadow-indigo-500/10"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          Respond
        </button>
        <button 
          onClick={() => onAction('flag', post)}
          disabled={post.flagged}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-slate-950 border border-slate-850 hover:bg-slate-800 disabled:opacity-50 text-slate-300 rounded-xl transition-colors"
        >
          <Flag className="w-3.5 h-3.5" />
          {post.flagged ? 'Flagged' : 'Flag'}
        </button>
        <button 
          onClick={() => onAction('investigate', post)}
          disabled={post.action_taken === 'investigate'}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-slate-950 border border-slate-850 hover:bg-slate-800 disabled:opacity-50 text-slate-300 rounded-xl transition-colors"
        >
          <Search className="w-3.5 h-3.5" />
          Investigate
        </button>
        <button 
          onClick={() => onAction('archive', post)}
          disabled={post.archived}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-slate-950 border border-slate-850 hover:bg-slate-800 disabled:opacity-50 text-slate-300 rounded-xl transition-colors"
        >
          <Archive className="w-3.5 h-3.5" />
          {post.archived ? 'Archived' : 'Archive'}
        </button>
      </div>
    </div>
  );
}

function PlatformIcon({ platform }: { platform: string }) {
  if (platform.toLowerCase().includes('xiaohongshu')) {
    return <div className="w-9 h-9 rounded-xl bg-red-950/40 border border-red-900/60 flex items-center justify-center text-red-400 font-bold text-xs select-none">XHS</div>;
  }
  if (platform.toLowerCase().includes('exa')) {
    return <div className="w-9 h-9 rounded-xl bg-indigo-950/40 border border-indigo-900/60 flex items-center justify-center text-indigo-400 font-bold text-xs select-none">EXA</div>;
  }
  return <Globe className="w-9 h-9 rounded-xl bg-slate-950 border border-slate-850 p-2 text-slate-400" />;
}

function RadarLoading({ progressPercent, progressStage }: { progressPercent: number, progressStage: string }) {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 select-none">
      <style>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse-ring {
          0% { transform: scale(0.95); opacity: 0.7; }
          50% { transform: scale(1.05); opacity: 1; }
          100% { transform: scale(0.95); opacity: 0.7; }
        }
        @keyframes radar-sweep {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .radar-spinner {
          animation: spin-slow 2s linear infinite;
        }
        .radar-pulse {
          animation: pulse-ring 2s ease-in-out infinite;
        }
        .radar-sweep {
          animation: radar-sweep 3s linear infinite;
          transform-origin: center;
        }
      `}</style>
      
      {/* Animated Radar Graphic */}
      <div className="relative mb-10">
        <div className="w-32 h-32 rounded-full border-4 border-indigo-950 flex items-center justify-center radar-pulse">
          <div className="w-24 h-24 rounded-full border-4 border-indigo-900 flex items-center justify-center">
            <div className="w-16 h-16 rounded-full border-4 border-indigo-700 flex items-center justify-center radar-spinner">
              <Radar className="w-8 h-8 text-indigo-400 animate-pulse" />
            </div>
          </div>
        </div>
        
        {/* Sweeping arc effect */}
        <div className="absolute inset-0 w-32 h-32 rounded-full overflow-hidden">
          <div 
            className="radar-sweep w-full h-full"
            style={{
              background: 'conic-gradient(from 0deg, transparent 0%, rgba(99, 102, 241, 0.15) 30%, transparent 45%)',
            }}
          />
        </div>
        
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2 w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-2 w-2 h-2 rounded-full bg-emerald-500 animate-pulse" style={{ animationDelay: '0.3s' }} />
        <div className="absolute top-1/2 -left-2 -translate-y-1/2 w-2 h-2 rounded-full bg-amber-500 animate-pulse" style={{ animationDelay: '0.6s' }} />
        <div className="absolute top-1/2 -right-2 -translate-y-1/2 w-2 h-2 rounded-full bg-rose-500 animate-pulse" style={{ animationDelay: '0.9s' }} />
      </div>
      
      {/* Progress Bar */}
      <div className="w-full max-w-md mb-6">
        <div className="flex justify-between text-sm mb-2 font-medium">
          <span className="text-indigo-400">{progressStage || "Scanning markets..."}</span>
          <span className="text-slate-500 font-mono">{Math.min(progressPercent, 98)}%</span>
        </div>
        <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-850">
          <div 
            className="bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-600 h-full rounded-full transition-all duration-1000 ease-out relative overflow-hidden"
            style={{ width: `${Math.min(progressPercent || 5, 98)}%` }}
          >
            <div className="absolute inset-0 bg-white/10 animate-pulse" />
          </div>
        </div>
      </div>
      
      {/* Animated Status Messages */}
      <div className="space-y-3 text-center">
        <div className="flex items-center gap-3 justify-center text-sm font-semibold text-slate-300">
          <Loader2 className="w-4.5 h-4.5 text-indigo-400 animate-spin" />
          <span>Running intelligence scan...</span>
        </div>
        <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
          Scanning Chinese and Russian markets for tourism intelligence, 
          safety alerts, and logistics trends. This may take 1-2 minutes.
        </p>
      </div>
    </div>
  );
}

function EmptyState({ onScan, clientId }: { onScan: () => void, clientId: string }) {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center p-6 max-w-2xl mx-auto select-none">
      <div className="bg-indigo-950/30 p-5 rounded-2xl mb-6 border border-indigo-900/60 shadow-lg shadow-indigo-500/5">
        <Globe className="w-12 h-12 text-indigo-400" />
      </div>
      <h2 className="text-2xl font-bold text-slate-100 mb-3">No Scan Data Available</h2>
      <p className="text-slate-400 mb-8 leading-relaxed text-sm max-w-md">
        Start your first geopolitical intelligence scan under client <strong className="text-indigo-300 font-semibold">{clientId}</strong> to monitor real-time sentiment, logistics alerts, and luxury travel demand.
      </p>
      <button 
        onClick={onScan}
        className="bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white px-8 py-3.5 rounded-xl font-semibold transition-all flex items-center gap-2 shadow-lg hover:shadow-xl hover:translate-y-[-1px]"
      >
        <Activity className="w-5 h-5" /> Initialize Radar Scan
      </button>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string, onRetry: () => void }) {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center p-6 max-w-lg mx-auto">
      <div className="bg-rose-950/30 p-5 rounded-full mb-6 border border-rose-900/60">
        <XCircle className="w-12 h-12 text-rose-500" />
      </div>
      <h2 className="text-2xl font-bold text-slate-100 mb-3">Scan Failed</h2>
      <p className="text-slate-400 mb-8 leading-relaxed bg-rose-950/20 p-4 rounded-xl border border-rose-900/40 text-sm">
        {message}
      </p>
      <button 
        onClick={onRetry}
        className="bg-slate-100 text-slate-900 px-6 py-3 rounded-xl font-semibold transition-colors hover:bg-slate-200 flex items-center gap-2"
      >
        <RefreshCw className="w-4 h-4" /> Try Again
      </button>
    </div>
  );
}