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


class ScanTriggerResponse(BaseModel):
    job_id: str
    status: str = "processing"