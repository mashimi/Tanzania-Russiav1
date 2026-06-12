"""Pydantic schemas for the TZ Tourism Radar API."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ScanRequest(BaseModel):
    client_id: str
    custom_keywords: Optional[List[str]] = []


class SocialPost(BaseModel):
    platform: str
    author: str
    content_snippet: str
    engagement: int
    is_crisis: bool


class MarketInsight(BaseModel):
    trend: str
    sentiment: str
    action: str
    posts: List[SocialPost]


class RadarReportResponse(BaseModel):
    id: str
    clientId: str
    status: str  # PROCESSING | COMPLETED | FAILED
    executiveSummary: str
    chinaInsights: List[Dict[str, Any]]
    russiaInsights: List[Dict[str, Any]]
    crisisAlerts: List[Dict[str, Any]]
    reportDate: Optional[str] = None
    raw_post_count: Optional[int] = 0


class ScanTriggerResponse(BaseModel):
    job_id: str
    status: str = "processing"


# -- Phase 3: Action & Search Schemas --
class PostActionRequest(BaseModel):
    action_type: str  # respond, flag, investigate, archive


class PostEngagement(BaseModel):
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    total_score: float = 0.0


class PostItem(BaseModel):
    id: str
    platform: str
    author: str
    author_followers: int = 0
    is_influencer: bool = False
    content_original: str = ""
    content_translated: str = ""
    url: str = ""
    published_at: str = ""
    engagement: PostEngagement = PostEngagement()
    sentiment: str = "neutral"
    is_crisis: bool = False
    topics: List[str] = []
    language: str = "unknown"
    screenshot_url: str = ""
    archived: bool = False
    flagged: bool = False
    action_taken: Optional[str] = None


class PostSearchParams(BaseModel):
    query: str = ""
    time_range: str = "24h"
    platform: str = "all"
    min_engagement: int = 0
    page: int = 1
    limit: int = 20


class PostSearchResult(BaseModel):
    posts: List[PostItem]
    total: int = 0
    page: int = 1
    limit: int = 20