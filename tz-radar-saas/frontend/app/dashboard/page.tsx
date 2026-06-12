"use client";

import { useState, useEffect, useCallback } from "react";
import {
  AlertTriangle, TrendingUp, TrendingDown, Minus,
  ExternalLink, Flag, Archive,
  MessageSquare, Search, Filter,
  Globe, Briefcase, Activity, RefreshCw, XCircle,
  Heart, Share2, Eye, Calendar, Clock,
  CheckCircle2, UserCheck, Hash, Languages,
  ChevronDown, ChevronUp, Loader2
} from "lucide-react";

// --- Types ---
interface PostEngagement {
  likes: number;
  comments: number;
  shares: number;
  views: number;
  total_score: number;
}

interface SocialPost {
  id?: string;
  platform: string;
  author: string;
  author_followers?: number;
  is_influencer?: boolean;
  content_snippet: string;
  content_original?: string;
  content_translated?: string;
  url?: string;
  published_at?: string;
  engagement?: PostEngagement | number;
  sentiment?: string;
  is_crisis: boolean;
  topics?: string[];
  language?: string;
  screenshot_url?: string;
  archived?: boolean;
  flagged?: boolean;
  action_taken?: string | null;
  source_keyword?: string;
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

export default function IntelligenceDashboard() {
  const [report, setReport] = useState<RadarReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  // Phase 2: Filters & Controls
  const [timeRange, setTimeRange] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("all");
  const [showTranslation, setShowTranslation] = useState(false);
  const [expandedPost, setExpandedPost] = useState<string | null>(null);

  const runScan = useCallback(async () => {
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const triggerRes = await fetch(`${API_URL}/api/v1/radar/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: "demo-client", custom_keywords: [] }),
      });

      if (!triggerRes.ok) throw new Error("Failed to trigger scan");

      const { job_id } = await triggerRes.json();
      setJobId(job_id);

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
  }, []);

  const handlePostAction = useCallback(async (actionType: string, post: SocialPost) => {
    const postId = post.id || post.url;
    if (!postId) return;

    try {
      await fetch(`${API_URL}/api/v1/posts/${encodeURIComponent(postId)}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_type: actionType }),
      });
    } catch (err) {
      console.error(`Failed to ${actionType} post:`, err);
    }
  }, []);

  // Collect all posts for search/filtering
  const getAllPosts = useCallback((): SocialPost[] => {
    if (!report) return [];
    const posts: SocialPost[] = [];
    for (const alert of report.crisisAlerts) posts.push(alert);
    for (const insight of [...report.chinaInsights, ...report.russiaInsights]) {
      posts.push(...insight.posts);
    }
    return posts;
  }, [report]);

  // Filtered posts based on search & platform
  const filteredPosts = getAllPosts().filter((post) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const snippet = (post.content_snippet || "").toLowerCase();
      const author = (post.author || "").toLowerCase();
      if (!snippet.includes(q) && !author.includes(q)) return false;
    }
    if (selectedPlatform !== "all" && !post.platform.toLowerCase().includes(selectedPlatform.toLowerCase())) {
      return false;
    }
    return true;
  });

  // Sort: crisis first, then by engagement
  const sortedPosts = [...filteredPosts].sort((a, b) => {
    if (a.is_crisis && !b.is_crisis) return -1;
    if (!a.is_crisis && b.is_crisis) return 1;
    const engA = typeof a.engagement === "number" ? a.engagement : (a.engagement as PostEngagement)?.total_score || 0;
    const engB = typeof b.engagement === "number" ? b.engagement : (b.engagement as PostEngagement)?.total_score || 0;
    return engB - engA;
  });

  // Render States
  if (loading) return <SkeletonDashboard />;
  if (error) return <ErrorState message={error} onRetry={runScan} />;
  if (!report) return <EmptyState onScan={runScan} />;

  const getCrisisPosts = () => sortedPosts.filter(p => p.is_crisis);
  const getNormalPosts = () => sortedPosts.filter(p => !p.is_crisis);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50">
      
      {/* Sticky Top Bar */}
      <div className="sticky top-0 z-10 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
            <div>
              <h1 className="text-xl font-bold tracking-tight flex items-center gap-2">
                <Globe className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                Geopolitical Intelligence
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {report.raw_post_count} posts collected &middot; Last scan: {report.reportDate ? new Date(report.reportDate).toLocaleString() : "N/A"}
              </p>
            </div>
            <button
              onClick={runScan}
              className="bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 shadow-sm hover:shadow-md text-sm shrink-0"
            >
              <RefreshCw className="w-4 h-4" /> New Scan
            </button>
          </div>

          {/* Phase 2: Search & Filter Controls */}
          <div className="flex flex-wrap items-center gap-3 mt-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search posts, topics, authors..."
                className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <select
              className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
            >
              <option value="all">All Platforms</option>
              <option value="xiao">XiaoHongShu</option>
              <option value="exa">Exa</option>
              <option value="ru">Russian Forums</option>
              <option value="cn">Chinese Forums</option>
            </select>

            <button
              onClick={() => setShowTranslation(!showTranslation)}
              className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
                showTranslation
                  ? "bg-indigo-600 text-white"
                  : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800"
              }`}
            >
              <Languages className="w-4 h-4" />
              {showTranslation ? "EN" : "中文"}
            </button>

            <div className="text-xs text-slate-500 dark:text-slate-400 ml-auto">
              {sortedPosts.length} post{sortedPosts.length !== 1 ? 's' : ''}
              {getCrisisPosts().length > 0 && (
                <span className="text-rose-500 ml-1">
                  &middot; {getCrisisPosts().length} crisis
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Crisis Alerts - Priority Display */}
        {getCrisisPosts().length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-rose-600 dark:text-rose-400 flex items-center gap-2 mb-3 uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4" />
              Critical Alerts ({getCrisisPosts().length})
            </h2>
            <div className="space-y-3">
              {getCrisisPosts().slice(0, 5).map((post, idx) => (
                <CrisisAlertCard
                  key={post.id || idx}
                  post={post}
                  expanded={expandedPost === (post.id || idx.toString())}
                  onToggle={() => setExpandedPost(expandedPost === (post.id || idx.toString()) ? null : (post.id || idx.toString()))}
                  onAction={(type) => handlePostAction(type, post)}
                  showTranslation={showTranslation}
                />
              ))}
            </div>
          </div>
        )}

        {/* Post Feed */}
        <div>
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2 mb-3 uppercase tracking-wider">
            <Activity className="w-4 h-4" />
            Intelligence Feed
          </h2>
          {getNormalPosts().length > 0 ? (
            <div className="space-y-3">
              {getNormalPosts().slice(0, 20).map((post, idx) => (
                <IntelligencePostCard
                  key={post.id || idx}
                  post={post}
                  expanded={expandedPost === (post.id || idx.toString())}
                  onToggle={() => setExpandedPost(expandedPost === (post.id || idx.toString()) ? null : (post.id || idx.toString()))}
                  onAction={(type) => handlePostAction(type, post)}
                  showTranslation={showTranslation}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400 dark:text-slate-500">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No posts matching your filters.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Post Card Components ---

function CrisisAlertCard({
  post, expanded, onToggle, onAction, showTranslation,
}: {
  post: SocialPost; expanded: boolean; onToggle: () => void; onAction: (type: string) => void; showTranslation: boolean;
}) {
  const eng = typeof post.engagement === "number" ? null : post.engagement as PostEngagement | undefined;

  return (
    <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/50 rounded-xl overflow-hidden transition-shadow hover:shadow-md">
      <div className="p-4 cursor-pointer" onClick={onToggle}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="bg-rose-100 dark:bg-rose-900/40 p-1.5 rounded-full shrink-0">
              <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{post.author}</span>
                <span className="text-xs px-2 py-0.5 bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-400 rounded-full font-medium">Crisis</span>
                {post.is_influencer && (
                  <span className="text-xs px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full font-medium">Influencer</span>
                )}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {post.platform} {post.published_at ? `• ${new Date(post.published_at).toLocaleDateString()}` : ""}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {post.url && (
              <a href={post.url} target="_blank" rel="noopener noreferrer" className="p-1.5 hover:bg-rose-100 dark:hover:bg-rose-900/40 rounded-lg" onClick={(e) => e.stopPropagation()}>
                <ExternalLink className="w-4 h-4 text-rose-500" />
              </a>
            )}
            {expanded ? <ChevronUp className="w-4 h-4 text-rose-400" /> : <ChevronDown className="w-4 h-4 text-rose-400" />}
          </div>
        </div>

        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300 line-clamp-2">
          {post.content_snippet}
        </p>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-rose-200 dark:border-rose-900/50 pt-3">
          {/* Topics */}
          {post.topics && post.topics.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {post.topics.map((topic) => (
                <span key={topic} className="px-2 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-md">
                  #{topic}
                </span>
              ))}
            </div>
          )}

          {/* Engagement */}
          {eng && (
            <div className="flex items-center gap-4 mb-3 text-xs text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1"><Heart className="w-3.5 h-3.5" />{eng.likes.toLocaleString()}</span>
              <span className="flex items-center gap-1"><MessageSquare className="w-3.5 h-3.5" />{eng.comments.toLocaleString()}</span>
              <span className="flex items-center gap-1"><Share2 className="w-3.5 h-3.5" />{eng.shares.toLocaleString()}</span>
              {eng.views > 0 && <span className="flex items-center gap-1"><Eye className="w-3.5 h-3.5" />{eng.views.toLocaleString()}</span>}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button onClick={() => onAction("respond")} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors">
              <MessageSquare className="w-3.5 h-3.5" /> Respond
            </button>
            <button onClick={() => onAction("flag")} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors">
              <Flag className="w-3.5 h-3.5" /> Flag
            </button>
            <button onClick={() => onAction("archive")} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors">
              <Archive className="w-3.5 h-3.5" /> Archive
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function IntelligencePostCard({
  post, expanded, onToggle, onAction, showTranslation,
}: {
  post: SocialPost; expanded: boolean; onToggle: () => void; onAction: (type: string) => void; showTranslation: boolean;
}) {
  const eng = typeof post.engagement === "number" ? null : post.engagement as PostEngagement | undefined;
  const sentimentColor =
    post.sentiment === "positive" ? "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900" :
    post.sentiment === "negative" ? "text-rose-600 bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-900" :
    "text-slate-600 bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700";

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden transition-shadow hover:shadow-md">
      <div className="p-4 cursor-pointer" onClick={onToggle}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <PlatformBadge platform={post.platform} />
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{post.author}</span>
                {post.is_influencer && (
                  <span className="text-xs px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full font-medium flex items-center gap-1">
                    <UserCheck className="w-3 h-3" /> Influencer
                  </span>
                )}
                {post.language && post.language !== "unknown" && (
                  <span className="text-xs text-slate-400 dark:text-slate-500 uppercase">{post.language}</span>
                )}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {post.platform} {post.published_at ? `• ${new Date(post.published_at).toLocaleDateString()}` : ""}
                {post.source_keyword && ` • "${post.source_keyword}"`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${sentimentColor}`}>
              {post.sentiment || "neutral"}
            </span>
            {post.url && (
              <a href={post.url} target="_blank" rel="noopener noreferrer" className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg" onClick={(e) => e.stopPropagation()}>
                <ExternalLink className="w-4 h-4 text-slate-400" />
              </a>
            )}
            {expanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </div>
        </div>

        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300 line-clamp-2 leading-relaxed">
          {post.content_snippet}
        </p>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-200 dark:border-slate-800 pt-3 space-y-3">
          {/* Topics */}
          {post.topics && post.topics.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {post.topics.map((topic) => (
                <span key={topic} className="px-2 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-md flex items-center gap-1">
                  <Hash className="w-3 h-3" />{topic}
                </span>
              ))}
            </div>
          )}

          {/* Engagement with Trend-like display */}
          {eng && (
            <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-2 rounded-lg">
              <span className="flex items-center gap-1"><Heart className="w-3.5 h-3.5 text-rose-400" />{eng.likes.toLocaleString()}</span>
              <span className="flex items-center gap-1"><MessageSquare className="w-3.5 h-3.5 text-blue-400" />{eng.comments.toLocaleString()}</span>
              <span className="flex items-center gap-1"><Share2 className="w-3.5 h-3.5 text-emerald-400" />{eng.shares.toLocaleString()}</span>
              {eng.views > 0 && <span className="flex items-center gap-1"><Eye className="w-3.5 h-3.5 text-indigo-400" />{eng.views.toLocaleString()}</span>}
              <span className="ml-auto font-semibold text-indigo-600 dark:text-indigo-400">
                Score: {eng.total_score.toFixed(0)}
              </span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button onClick={() => onAction("respond")} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors">
              <MessageSquare className="w-3.5 h-3.5" /> Respond
            </button>
            <button onClick={() => onAction("flag")} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors">
              <Flag className="w-3.5 h-3.5" /> Flag
            </button>
            <button onClick={() => onAction("investigate")} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors">
              <Search className="w-3.5 h-3.5" /> Investigate
            </button>
            <button onClick={() => onAction("archive")} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg transition-colors">
              <Archive className="w-3.5 h-3.5" /> Archive
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function PlatformBadge({ platform }: { platform: string }) {
  const colors: Record<string, string> = {
    "XiaoHongShu": "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-400",
    "Exa (CN)": "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400",
    "Exa (RU)": "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400",
  };
  const color = colors[platform] || "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${color}`}>
      {platform}
    </span>
  );
}

// --- Skeleton, Empty, Error States ---

function SkeletonDashboard() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 max-w-7xl mx-auto animate-pulse">
      <div className="space-y-4">
        <div className="h-12 bg-slate-200 dark:bg-slate-800 rounded-xl w-full"></div>
        <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded-lg w-full"></div>
        {[1, 2, 3].map(i => (
          <div key={i} className="h-24 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        ))}
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

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
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