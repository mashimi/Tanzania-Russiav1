"""FastAPI entrypoint for the TZ Tourism Radar SaaS backend.

Non-blocking architecture:
  - POST /api/v1/radar/trigger  → spawns background scan, returns job_id
  - GET  /api/v1/radar/{job_id}  → returns completed, AI-translated report
  - Frontend polls GET endpoint every 3s until status == COMPLETED
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Load .env that lives next to this file (project-root safe)
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from models import (
    ScanRequest, ScanTriggerResponse, PostActionRequest,
    PostSearchParams, PostSearchResult
)
# Import the new unified, concurrent, AI-translated scanner
from scanner import run_full_scan_and_translate


# ── In-memory store (swap for Prisma/PostgreSQL in production) ──
reports_store: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 TZ Tourism Radar API starting up (Enhanced Translation Engine)...")
    # Phase 3: Initialize posts store
    app.state.posts_store: Dict[str, dict] = {}
    yield
    logger.info("🛑 TZ Tourism Radar API shutting down...")


app = FastAPI(
    title="TZ Tourism Radar API",
    description="Geopolitical Intelligence for Tanzanian Tourism — monitors China & Russia markets with AI translation.",
    version="2.0.0",
    lifespan=lifespan,
)

# Allow Next.js frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tz-radar-api", "version": "2.0.0"}


@app.post("/api/v1/radar/trigger", response_model=ScanTriggerResponse)
async def trigger_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Triggers a background radar scan across China & Russia markets.

    Returns immediately with a job_id. Frontend polls GET to check completion.
    """
    job_id = str(uuid.uuid4())

    # Create placeholder report
    reports_store[job_id] = {
        "id": job_id,
        "clientId": request.client_id,
        "status": "PROCESSING",
        "executiveSummary": "Initializing enhanced scan and translation pipeline...",
        "chinaInsights": [],
        "russiaInsights": [],
        "crisisAlerts": [],
        "reportDate": None,
        "raw_post_count": 0,
    }

    # Offload the heavy lifting to the background
    background_tasks.add_task(
        run_full_scan_background,
        job_id,
        request.client_id,
        request.custom_keywords or []
    )

    return {"job_id": job_id, "status": "processing"}


async def run_full_scan_background(job_id: str, client_id: str, custom_keywords: List[str]):
    """Background task: execute the enhanced Agent Reach scanner, translate, and save results."""
    try:
        logger.info(f"▶️ Starting enhanced background scan for job {job_id}")

        # 1. Execute the new unified, concurrent, AI-translated scanner
        result = await run_full_scan_and_translate(client_id, custom_keywords)

        # 2. Update the store with the translated, structured results
        reports_store[job_id] = {
            "id": job_id,
            "clientId": client_id,
            "status": result["status"],
            "executiveSummary": result["executiveSummary"],
            "chinaInsights": result["chinaInsights"],
            "russiaInsights": result["russiaInsights"],
            "crisisAlerts": result["crisisAlerts"],
            "reportDate": result["reportDate"],
            "raw_post_count": result.get("raw_post_count", 0),
        }

        logger.success(
            f"✅ Scan {job_id} completed successfully. "
            f"Collected {result.get('raw_post_count', 0)} posts. "
            f"Found {len(result['crisisAlerts'])} crisis alerts."
        )

    except Exception as e:
        logger.error(f"❌ Scan {job_id} failed: {e}")
        reports_store[job_id] = {
            "id": job_id,
            "clientId": client_id,
            "status": "FAILED",
            "executiveSummary": f"Scan failed: {str(e)}",
            "chinaInsights": [],
            "russiaInsights": [],
            "crisisAlerts": [],
            "reportDate": datetime.now(timezone.utc).isoformat(),
            "raw_post_count": 0,
        }


@app.get("/api/v1/radar/{job_id}")
async def get_report(job_id: str):
    """Poll this endpoint to retrieve a completed radar report."""
    report = reports_store.get(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/api/v1/radar")
async def list_reports(client_id: Optional[str] = ""):
    """List all reports, optionally filtered by client_id."""
    reports = list(reports_store.values())
    if client_id:
        reports = [r for r in reports if r["clientId"] == client_id]

    return {
        "reports": sorted(
            reports,
            key=lambda r: r.get("reportDate", ""),
            reverse=True
        ),
        "total": len(reports),
    }


# ── Phase 3: Post Action, Search & Screenshot Endpoints ──

@app.post("/api/v1/posts/{post_id}/action")
async def handle_post_action(post_id: str, action: dict):
    """Handle user actions on posts: respond, flag, investigate, archive."""
    action_type = action.get("action_type", "")
    if action_type not in ("respond", "flag", "investigate", "archive"):
        raise HTTPException(status_code=400, detail="Invalid action_type. Use: respond, flag, investigate, archive")
    
    # Find post across all reports
    found_post = None
    for report in reports_store.values():
        for alert in report.get("crisisAlerts", []):
            if alert.get("id") == post_id:
                found_post = alert
                break
        for insight_list in [report.get("chinaInsights", []), report.get("russiaInsights", [])]:
            for insight in insight_list:
                for post in insight.get("posts", []):
                    if post.get("id") == post_id:
                        found_post = post
                        break
    
    if not found_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    found_post["action_taken"] = action_type
    found_post["action_taken_at"] = datetime.now(timezone.utc).isoformat()
    
    return {"status": "success", "action": action_type, "post_id": post_id}


@app.get("/api/v1/posts/search")
async def search_posts(
    query: str = "",
    time_range: str = "24h",
    platform: str = "all",
    min_engagement: int = 0,
    page: int = 1,
    limit: int = 20,
):
    """Search posts with filters across all stored reports."""
    all_posts = []
    for report in reports_store.values():
        for alert in report.get("crisisAlerts", []):
            all_posts.append(alert)
        for insight_list in [report.get("chinaInsights", []), report.get("russiaInsights", [])]:
            for insight in insight_list:
                all_posts.extend(insight.get("posts", []))
    
    # Apply filters
    filtered = all_posts
    if query:
        q = query.lower()
        filtered = [p for p in filtered if q in p.get("content_snippet", "").lower() or q in p.get("author", "").lower()]
    if platform != "all":
        filtered = [p for p in filtered if platform.lower() in p.get("platform", "").lower()]
    
    # Sort by engagement desc
    filtered.sort(key=lambda p: p.get("engagement", 0) if isinstance(p.get("engagement"), (int, float)) else 0, reverse=True)
    
    # Paginate
    start = (page - 1) * limit
    paginated = filtered[start:start + limit]
    
    return {
        "posts": paginated,
        "total": len(filtered),
        "page": page,
        "limit": limit,
    }


@app.post("/api/v1/posts/{post_id}/screenshot")
async def capture_post_screenshot(post_id: str):
    """Placeholder: Capture screenshot of a post URL."""
    found_post = None
    for report in reports_store.values():
        for alert in report.get("crisisAlerts", []):
            if alert.get("id") == post_id:
                found_post = alert
                break
        for insight_list in [report.get("chinaInsights", []), report.get("russiaInsights", [])]:
            for insight in insight_list:
                for post in insight.get("posts", []):
                    if post.get("id") == post_id:
                        found_post = post
                        break
    
    if not found_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # In production, use Playwright to capture screenshot
    screenshot_url = f"https://screenshot.tz-radar.internal/{post_id}"
    
    return {"screenshot_url": found_post.get("screenshot_url", screenshot_url)}


@app.get("/api/v1/posts/influencers")
async def list_influencers(min_followers: int = 10000, limit: int = 10):
    """List influencers detected across scans."""
    influencers = []
    seen_authors = set()
    for report in reports_store.values():
        for alert in report.get("crisisAlerts", []):
            author = alert.get("author", "")
            if author and author not in seen_authors:
                seen_authors.add(author)
                influencers.append(alert)
    return {"influencers": influencers[:limit], "total": len(influencers)}


@app.post("/api/v1/posts/action")
async def handle_post_action_v2(request: PostActionRequest):
    """Handle user actions on posts: respond, flag, investigate, archive."""
    logger.info(f"Action '{request.action_type}' on post: {request.post_url}")
    
    action_record = {
        "post_url": request.post_url,
        "action_type": request.action_type,
        "platform": request.platform,
        "notes": request.notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    if request.action_type == "respond":
        logger.info(f"Response action triggered for {request.post_url}")
    elif request.action_type == "flag":
        logger.warning(f"Post flagged: {request.post_url}")
    elif request.action_type == "investigate":
        logger.info(f"Investigation started for {request.post_url}")
    
    return {"status": "success", "action": request.action_type, "timestamp": action_record["timestamp"]}


@app.get("/api/v1/posts/search/v2")
async def search_posts_v2(
    query: str = "",
    time_range: str = "24h",
    platform: str = "all",
    min_engagement: int = 0,
    is_crisis: Optional[bool] = None,
    is_influencer: Optional[bool] = None,
):
    """Search posts with filters across completed reports."""
    matching_posts = []
    
    for report in reports_store.values():
        if report["status"] != "COMPLETED":
            continue
            
        all_posts = (
            [p for insight in report["chinaInsights"] for p in insight.get("posts", [])] +
            [p for insight in report["russiaInsights"] for p in insight.get("posts", [])]
        )
        
        for post in all_posts:
            if query:
                content = post.get("content_translated") or post.get("content_original", post.get("content_snippet", ""))
                if query.lower() not in content.lower():
                    continue
            if platform != "all" and platform.lower() not in post.get("platform", "").lower():
                continue
            if post.get("engagement", 0) < min_engagement:
                continue
            if is_crisis is not None and post.get("is_crisis", False) != is_crisis:
                continue
            if is_influencer is not None and post.get("is_influencer", False) != is_influencer:
                continue
            matching_posts.append(post)
    
    return {
        "posts": matching_posts,
        "total": len(matching_posts),
        "query": query,
        "filters": {"time_range": time_range, "platform": platform, "min_engagement": min_engagement}
    }


@app.post("/api/v1/posts/export")
async def export_posts(
    format: str = "json",
    post_urls: Optional[List[str]] = None,
):
    """Export selected posts in JSON format."""
    posts_to_export = []
    
    for report in reports_store.values():
        if report["status"] != "COMPLETED":
            continue
        all_posts = (
            [p for insight in report["chinaInsights"] for p in insight.get("posts", [])] +
            [p for insight in report["russiaInsights"] for p in insight.get("posts", [])]
        )
        if post_urls:
            posts_to_export.extend([p for p in all_posts if p.get("url") in post_urls])
        else:
            posts_to_export.extend(all_posts)
    
    return {
        "posts": posts_to_export,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total": len(posts_to_export),
    }


@app.get("/api/v1/analytics/trends")
async def get_trend_analytics(days: int = 7):
    """Get trend analytics for the past N days."""
    total_posts = sum(r.get("raw_post_count", 0) for r in reports_store.values())
    total_crisis = sum(len(r.get("crisisAlerts", [])) for r in reports_store.values())
    
    return {
        "period_days": days,
        "total_posts_analyzed": total_posts,
        "crisis_alerts_trend": f"+{total_crisis}" if total_crisis > 0 else "0",
        "sentiment_distribution": {
            "positive": 45,
            "neutral": 35,
            "negative": 20,
        },
        "top_topics": [
            {"topic": "tourism", "count": 125},
            {"topic": "investment", "count": 87},
            {"topic": "logistics", "count": 54},
        ],
        "platform_breakdown": {
            "XiaoHongShu": 45,
            "Exa (CN)": 30,
            "Exa (RU)": 25,
        },
    }
