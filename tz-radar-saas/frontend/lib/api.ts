import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export interface EngagementDetails {
  likes: number;
  comments: number;
  shares: number;
  views: number;
}

export interface SocialPost {
  platform: string;
  author: string;
  content_snippet: string;
  engagement: number;
  is_crisis: boolean;
  author_followers?: number;
  is_influencer?: boolean;
  content_original?: string;
  content_translated?: string;
  url?: string;
  published_at?: string;
  screenshot_url?: string | null;
  topics?: string[];
  language?: string;
  trend_percentage?: number;
  action_taken?: string | null;
  flagged?: boolean;
  archived?: boolean;
  engagement_details?: EngagementDetails;
}

export interface MarketInsight {
  trend: string;
  sentiment: string;
  action: string;
  posts: SocialPost[];
}

export interface RadarReport {
  id: string;
  clientId: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  executiveSummary: string;
  chinaInsights: MarketInsight[];
  russiaInsights: MarketInsight[];
  crisisAlerts: SocialPost[];
  reportDate: string | null;
  marketReadinessScore?: number;
  dailyMentions?: number;
  sentimentScore?: number;
  raw_post_count?: number;
  progress_percent?: number;
  progress_stage?: string;
}

export interface ScanTriggerResponse {
  job_id: string;
  status: string;
}

// ── API Functions ──

export async function triggerScan(
  clientId: string,
  customKeywords: string[] = []
): Promise<ScanTriggerResponse> {
  const res = await api.post("/api/v1/radar/trigger", {
    client_id: clientId,
    custom_keywords: customKeywords,
  });
  return res.data;
}

export async function getReport(jobId: string): Promise<RadarReport> {
  const res = await api.get(`/api/v1/radar/${jobId}`);
  return res.data;
}

export async function listReports(
  clientId: string = ""
): Promise<{ reports: RadarReport[]; total: number }> {
  const params = clientId ? { client_id: clientId } : {};
  const res = await api.get("/api/v1/radar", { params });
  return res.data;
}