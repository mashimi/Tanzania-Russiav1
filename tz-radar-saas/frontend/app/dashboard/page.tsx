"use client";

import { useState, useEffect } from "react";
import { 
  AlertTriangle, TrendingUp, TrendingDown, Minus,
  ExternalLink, Flag, Archive, Search, Filter,
  MessageSquare, Eye, Heart, Share2, RefreshCw,
  CheckCircle2, XCircle, Globe, Briefcase, Loader2,
  ShieldCheck, Activity, Download, Calendar
} from "lucide-react";

// --- Types ---
interface EngagementDetails {
  likes: number;
  comments: number;
  shares: number;
  views: number;
}

interface SocialPost {
  platform: string;
  author: string;
  author_followers: number;
  is_influencer: boolean;
  content_original: string;
  content_translated: string;
  engagement: number;
  engagement_details: EngagementDetails;
  is_crisis: boolean;
  url: string;
  published_at: string;
  screenshot_url: string | null;
  topics: string[];
  language: string;
  trend_percentage: number;
  action_taken?: string | null;
  flagged?: boolean;
  archived?: boolean;
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
  
  // Filter & Search State
  const [timeRange, setTimeRange] = useState("24h");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState("all");
  const [showTranslation, setShowTranslation] = useState(false);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [minEngagement, setMinEngagement] = useState(0);
  const [showCrisisOnly, setShowCrisisOnly] = useState(false);
  const [showInfluencersOnly, setShowInfluencersOnly] = useState(false);

  const runScan = async () => {
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
  };

  const handlePostAction = async (action: string, post: SocialPost) => {
    try {
      await fetch(`${API_URL}/api/v1/posts/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_url: post.url,
          action_type: action,
          platform: post.platform,
        }),
      });
      
      // Update local state
      if (report) {
        const updatedReport = { ...report };
        const updatePostInInsights = (insights: MarketInsight[]) => {
          insights.forEach(insight => {
            const postIndex = insight.posts.findIndex(p => p.url === post.url);
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
      console.error(`Failed to ${action} post:`, err);
    }
  };

  // Filter posts based on criteria
  const filterPosts = (posts: SocialPost[]) => {
    return posts.filter(post => {
      if (showCrisisOnly && !post.is_crisis) return false;
      if (showInfluencersOnly && !post.is_influencer) return false;
      if (post.engagement < minEngagement) return false;
      if (selectedPlatform !== "all" && !post.platform.toLowerCase().includes(selectedPlatform.toLowerCase())) return false;
      if (selectedTopics.length > 0 && !post.topics.some(t => selectedTopics.includes(t))) return false;
      if (searchQuery) {
        const searchLower = searchQuery.toLowerCase();
        const content = showTranslation && post.content_translated ? post.content_translated : post.content_original;
        if (!content.toLowerCase().includes(searchLower) && 
            !post.author.toLowerCase().includes(searchLower) &&
            !post.topics.some(t => t.toLowerCase().includes(searchLower))) {
          return false;
        }
      }
      return true;
    });
  };

  if (loading) return <SkeletonDashboard />;
  if (error) return <ErrorState message={error} onRetry={runScan} />;
  if (!report) return <EmptyState onScan={runScan} />;

  const allPosts = [
    ...report.chinaInsights.flatMap(i => i.posts),
    ...report.russiaInsights.flatMap(i => i.posts),
  ];

  const filteredPosts = filterPosts(allPosts);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 p-6 space-y-6 max-w-7xl mx-auto">
      
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
              {report.crisisAlerts.length} high-priority alert(s) require immediate attention.
            </p>
          </div>
        </div>
      )}

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Posts Analyzed" value={report.raw_post_count.toString()} icon={Globe} color="blue" />
        <KPICard title="Crisis Alerts" value={report.crisisAlerts.length.toString()} icon={AlertTriangle} color="rose" />
        <KPICard title="China Insights" value={report.chinaInsights.length.toString()} icon={TrendingUp} color="emerald" />
        <KPICard title="Russia Insights" value={report.russiaInsights.length.toString()} icon={ShieldCheck} color="indigo" />
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 space-y-4">
        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-[250px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search posts, authors, topics..."
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          <select 
            className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="custom">Custom range</option>
          </select>
          
          <select
            className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950"
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
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${showTranslation ? 'bg-indigo-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'}`}
          >
            {showTranslation ? 'EN' : '中文/РУС'}
          </button>
        </div>
        
        <div className="flex flex-wrap gap-3 items-center">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showCrisisOnly}
              onChange={(e) => setShowCrisisOnly(e.target.checked)}
              className="rounded border-slate-300 text-rose-600 focus:ring-rose-500"
            />
            <span className="text-slate-700 dark:text-slate-300">Crisis only</span>
          </label>
          
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showInfluencersOnly}
              onChange={(e) => setShowInfluencersOnly(e.target.checked)}
              className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
            />
            <span className="text-slate-700 dark:text-slate-300">Influencers only</span>
          </label>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-700 dark:text-slate-300">Min engagement:</span>
            <input
              type="number"
              value={minEngagement}
              onChange={(e) => setMinEngagement(Number(e.target.value))}
              className="w-24 px-3 py-1 rounded border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-sm"
              placeholder="0"
            />
          </div>
          
          <div className="flex items-center gap-2 ml-auto">
            <span className="text-sm text-slate-500 dark:text-slate-400">
              Showing {filteredPosts.length} of {allPosts.length} posts
            </span>
          </div>
        </div>
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

      {/* Posts Feed */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-500" />
          Intelligence Feed
        </h2>
        
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
          <div className="text-center py-12 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl">
            <Search className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
            <p className="text-slate-500 dark:text-slate-400">No posts match your filters</p>
            <button 
              onClick={() => {
                setSearchQuery("");
                setShowCrisisOnly(false);
                setShowInfluencersOnly(false);
                setMinEngagement(0);
                setSelectedPlatform("all");
              }}
              className="mt-3 text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Clear all filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// --- Sub-components ---

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

function IntelligencePostCard({ post, showTranslation, onAction }: { post: SocialPost, showTranslation: boolean, onAction: (action: string, post: SocialPost) => void }) {
  const trend = post.trend_percentage;
  const content = showTranslation && post.content_translated ? post.content_translated : post.content_original;
  
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <PlatformIcon platform={post.platform} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold">{post.author}</span>
              {post.is_influencer && (
                <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-xs rounded-full font-medium flex items-center gap-1">
                  ⭐ {post.author_followers.toLocaleString()} followers
                </span>
              )}
              {post.is_crisis && (
                <span className="px-2 py-0.5 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-400 text-xs rounded-full font-medium">
                  🚨 Crisis
                </span>
              )}
            </div>
            <div className="text-sm text-slate-500 dark:text-slate-400 flex items-center gap-2">
              <span>{post.platform}</span>
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
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
              title="View screenshot"
            >
              <Eye className="w-4 h-4" />
            </a>
          )}
          <a 
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
            title="View original post"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Content */}
      <div className="mb-4">
        <p className="text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
          {content}
        </p>
        {showTranslation && post.content_translated && post.content_original !== post.content_translated && (
          <div className="mt-3 p-3 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-1 font-medium">Original:</p>
            <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">{post.content_original}</p>
          </div>
        )}
      </div>

      {/* Engagement Metrics */}
      <div className="flex items-center gap-6 mb-4">
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <Heart className="w-4 h-4" />
          <span className="text-sm font-medium">{post.engagement_details.likes.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <MessageSquare className="w-4 h-4" />
          <span className="text-sm font-medium">{post.engagement_details.comments.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <Share2 className="w-4 h-4" />
          <span className="text-sm font-medium">{post.engagement_details.shares.toLocaleString()}</span>
        </div>
        {post.engagement_details.views > 0 && (
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
            <Eye className="w-4 h-4" />
            <span className="text-sm font-medium">{post.engagement_details.views.toLocaleString()}</span>
          </div>
        )}
        
        {/* Trend Indicator */}
        {trend !== 0 && (
          <div className={`flex items-center gap-1 ml-auto ${trend > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
            {trend > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span className="text-sm font-medium">{Math.abs(trend)}%</span>
          </div>
        )}
      </div>

      {/* Topics & Sentiment */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {post.topics.map(topic => (
          <span key={topic} className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs rounded-md">
            #{topic}
          </span>
        ))}
        {post.action_taken && (
          <span className="ml-auto px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 text-xs rounded-md font-medium flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> {post.action_taken}
          </span>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-3 border-t border-slate-200 dark:border-slate-800">
        <button 
          onClick={() => onAction('respond', post)}
          disabled={post.action_taken === 'respond'}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg transition-colors"
        >
          <MessageSquare className="w-4 h-4" />
          Respond
        </button>
        <button 
          onClick={() => onAction('flag', post)}
          disabled={post.flagged}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50 rounded-lg transition-colors"
        >
          <Flag className="w-4 h-4" />
          {post.flagged ? 'Flagged' : 'Flag'}
        </button>
        <button 
          onClick={() => onAction('investigate', post)}
          disabled={post.action_taken === 'investigate'}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50 rounded-lg transition-colors"
        >
          <Search className="w-4 h-4" />
          Investigate
        </button>
        <button 
          onClick={() => onAction('archive', post)}
          disabled={post.archived}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50 rounded-lg transition-colors"
        >
          <Archive className="w-4 h-4" />
          {post.archived ? 'Archived' : 'Archive'}
        </button>
      </div>
    </div>
  );
}

function PlatformIcon({ platform }: { platform: string }) {
  if (platform.toLowerCase().includes('xiaohongshu')) {
    return <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-600 dark:text-red-400 font-bold text-xs">XHS</div>;
  }
  if (platform.toLowerCase().includes('exa')) {
    return <div className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-xs">EXA</div>;
  }
  return <Globe className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 p-2 text-slate-600 dark:text-slate-400" />;
}

function SkeletonDashboard() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 space-y-6 max-w-7xl mx-auto animate-pulse">
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
      
      <div className="h-32 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
      <div className="h-40 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-48 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
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