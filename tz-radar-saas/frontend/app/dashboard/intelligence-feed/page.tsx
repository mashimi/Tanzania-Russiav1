"use client";

import { useState, useEffect } from "react";
import { 
  Search, Filter, ExternalLink, Flag, Archive, 
  MessageSquare, Eye, Heart, Share2, TrendingUp, 
  TrendingDown, AlertTriangle, Star, Download,
  RefreshCw, CheckCircle2, XCircle, Globe
} from "lucide-react";

// --- Types ---
interface EngagementDetails {
  likes: number;
  comments: number;
  shares: number;
  views: number;
}

interface IntelligencePost {
  id?: string;
  platform: string;
  author: string;
  author_followers?: number;
  is_influencer?: boolean;
  content_original: string;
  content_translated?: string;
  engagement: number;
  engagement_details?: EngagementDetails;
  is_crisis: boolean;
  url: string;
  published_at: string;
  screenshot_url?: string | null;
  topics?: string[];
  language?: string;
  trend_percentage?: number;
  action_taken?: string | null;
  flagged?: boolean;
  archived?: boolean;
  report_id?: string;
  report_date?: string;
}

interface FeedResponse {
  posts: IntelligencePost[];
  total: number;
  has_more: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function IntelligenceFeedPage() {
  // State
  const [posts, setPosts] = useState<IntelligencePost[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [timeRange, setTimeRange] = useState("24h");
  const [selectedPlatform, setSelectedPlatform] = useState("all");
  const [showTranslation, setShowTranslation] = useState(false);
  const [showCrisisOnly, setShowCrisisOnly] = useState(false);
  const [showInfluencersOnly, setShowInfluencersOnly] = useState(false);
  const [minEngagement, setMinEngagement] = useState(0);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // Fetch feed
  const fetchFeed = async (reset = false) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        query: searchQuery,
        time_range: timeRange,
        platform: selectedPlatform,
        min_engagement: minEngagement.toString(),
        limit: "50",
        offset: reset ? "0" : offset.toString(),
      });

      if (showCrisisOnly) params.append("is_crisis", "true");
      if (showInfluencersOnly) params.append("is_influencer", "true");

      const response = await fetch(`${API_URL}/api/v1/posts/search?${params}`);
      const data: FeedResponse = await response.json();

      if (reset) {
        setPosts(data.posts);
      } else {
        setPosts(prev => [...prev, ...data.posts]);
      }

      setTotal(data.total);
      setHasMore(data.has_more);
      setOffset(reset ? 50 : offset + 50);
    } catch (error) {
      console.error("Failed to fetch feed:", error);
    } finally {
      setLoading(false);
    }
  };

  // Initial load / reload on filter change
  useEffect(() => {
    fetchFeed(true);
  }, [searchQuery, timeRange, selectedPlatform, minEngagement, showCrisisOnly, showInfluencersOnly]);

  // Handle post action
  const handlePostAction = async (action: string, post: IntelligencePost) => {
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
      setPosts(prev => prev.map(p => {
        if (p.url === post.url) {
          return {
            ...p,
            action_taken: action,
            flagged: action === 'flag' ? true : p.flagged,
            archived: action === 'archive' ? true : p.archived,
          };
        }
        return p;
      }));
    } catch (error) {
      console.error(`Failed to ${action} post:`, error);
    }
  };

  // Export posts
  const handleExport = async (format: 'csv' | 'json') => {
    try {
      const response = await fetch(`${API_URL}/api/v1/posts/export?format=${format}`);
      const data = await response.json();
      
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `intelligence-feed-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
      } else {
        const blob = new Blob([data.csv_data], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `intelligence-feed-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
      }
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
              <Eye className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
              Live Intelligence Feed
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1.5">
              Real-time social media monitoring across China & Russia markets • {total.toLocaleString()} posts analyzed
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleExport('json')}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export JSON
            </button>
            <button
              onClick={() => handleExport('csv')}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Filter Bar */}
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
              <span className="text-slate-700 dark:text-slate-300 flex items-center gap-1">
                <AlertTriangle className="w-4 h-4" />
                Crisis only
              </span>
            </label>
            
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={showInfluencersOnly}
                onChange={(e) => setShowInfluencersOnly(e.target.checked)}
                className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
              />
              <span className="text-slate-700 dark:text-slate-300 flex items-center gap-1">
                <Star className="w-4 h-4" />
                Influencers only
              </span>
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
                Showing {posts.length} of {total.toLocaleString()} posts
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Posts Feed */}
      <div className="max-w-7xl mx-auto space-y-4">
        {loading && posts.length === 0 ? (
          <FeedSkeleton />
        ) : posts.length > 0 ? (
          <>
            {posts.map((post, idx) => (
              <IntelligencePostCard 
                key={`${post.url}-${idx}`} 
                post={post} 
                showTranslation={showTranslation}
                onAction={handlePostAction}
              />
            ))}
            
            {hasMore && (
              <div className="flex justify-center py-6">
                <button
                  onClick={() => fetchFeed(false)}
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                  Load More Posts
                </button>
              </div>
            )}
          </>
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

// --- Feed Skeleton Component ---
function FeedSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map(i => (
        <div key={i} className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-800" />
            <div className="space-y-2">
              <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-48" />
              <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-72" />
            </div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded" />
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
          </div>
          <div className="flex gap-6">
            {[1, 2, 3, 4].map(j => (
              <div key={j} className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-16" />
            ))}
          </div>
          <div className="flex gap-2 pt-3 border-t border-slate-200 dark:border-slate-800">
            {[1, 2, 3, 4].map(j => (
              <div key={j} className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-20" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// --- Post Card Component ---
function IntelligencePostCard({ 
  post, 
  showTranslation, 
  onAction 
}: { 
  post: IntelligencePost; 
  showTranslation: boolean;
  onAction: (action: string, post: IntelligencePost) => void;
}) {
  const trend = post.trend_percentage || 0;
  const content = showTranslation && post.content_translated 
    ? post.content_translated 
    : post.content_original;
  
  const engagement = post.engagement_details || {
    likes: post.engagement,
    comments: 0,
    shares: 0,
    views: 0,
  };

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
                  <Star className="w-3 h-3" />
                  {post.author_followers?.toLocaleString() || 'Unknown'} followers
                </span>
              )}
              {post.is_crisis && (
                <span className="px-2 py-0.5 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-400 text-xs rounded-full font-medium">
                  <AlertTriangle className="w-3 h-3 inline" />
                  Crisis
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
          <span className="text-sm font-medium">{engagement.likes.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <MessageSquare className="w-4 h-4" />
          <span className="text-sm font-medium">{engagement.comments.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <Share2 className="w-4 h-4" />
          <span className="text-sm font-medium">{engagement.shares.toLocaleString()}</span>
        </div>
        {engagement.views > 0 && (
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
            <Eye className="w-4 h-4" />
            <span className="text-sm font-medium">{formatNumber(engagement.views)}</span>
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
        {post.topics?.map(topic => (
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

// --- Helper Components ---
function PlatformIcon({ platform }: { platform: string }) {
  if (platform.toLowerCase().includes('xiaohongshu')) {
    return (
      <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-600 dark:text-red-400 font-bold text-xs">
        XHS
      </div>
    );
  }
  if (platform.toLowerCase().includes('exa')) {
    return (
      <div className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-xs">
        EXA
      </div>
    );
  }
  return (
    <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-400">
      <Eye className="w-5 h-5" />
    </div>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}