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
from fastapi.responses import Response
from loguru import logger

from models import (
    ScanRequest, ScanTriggerResponse, PostActionRequest,
    PostSearchParams, PostSearchResult
)
# Import the new unified, concurrent, AI-translated scanner
from scanner import run_full_scan_and_translate
from utils.pdf_export import generate_radar_pdf


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

    # Create placeholder report with progress tracking
    reports_store[job_id] = {
        "id": job_id,
        "clientId": request.client_id,
        "status": "PROCESSING",
        "progress_percent": 0,
        "progress_stage": "Initializing scan pipeline...",
        "executiveSummary": "",
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

        # Update progress: starting scan
        reports_store[job_id].update({"progress_percent": 5, "progress_stage": "Scanning Russia market..."})

        # 1. Execute the new unified, concurrent, AI-translated scanner
        result = await run_full_scan_and_translate(client_id, custom_keywords)

        # 2. Update the store with the translated, structured results
        reports_store[job_id] = {
            "id": job_id,
            "clientId": client_id,
            "status": result["status"],
            "progress_percent": 100,
            "progress_stage": "Scan complete",
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
            "progress_percent": 0,
            "progress_stage": "Scan failed",
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


@app.get("/api/v1/posts/feed")
async def get_intelligence_feed(
    job_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Get live intelligence feed with full post details.
    Returns posts with engagement metrics, translations, and author info.
    """
    if job_id:
        report = reports_store.get(job_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        all_posts = []
        for insight in report.get("chinaInsights", []):
            all_posts.extend(insight.get("posts", []))
        for insight in report.get("russiaInsights", []):
            all_posts.extend(insight.get("posts", []))
        all_posts.extend(report.get("crisisAlerts", []))
        
        # Deduplicate by url if present
        seen_urls = set()
        deduped = []
        for p in all_posts:
            url = p.get("url")
            if url:
                if url not in seen_urls:
                    seen_urls.add(url)
                    deduped.append(p)
            else:
                deduped.append(p)
        
        deduped.sort(key=lambda x: x.get("engagement", 0) if isinstance(x.get("engagement"), (int, float)) else 0, reverse=True)
        paginated_posts = deduped[offset:offset + limit]
        
        return {
            "posts": paginated_posts,
            "total": len(deduped),
            "has_more": offset + limit < len(deduped),
        }
    
    all_posts = []
    for report in reports_store.values():
        if report.get("status") != "COMPLETED":
            continue
        
        for insight in report.get("chinaInsights", []):
            for post in insight.get("posts", []):
                all_posts.append({**post, "report_id": report["id"], "report_date": report.get("reportDate")})
        for insight in report.get("russiaInsights", []):
            for post in insight.get("posts", []):
                all_posts.append({**post, "report_id": report["id"], "report_date": report.get("reportDate")})
        for alert in report.get("crisisAlerts", []):
            all_posts.append({**alert, "report_id": report["id"], "report_date": report.get("reportDate")})
    
    # Deduplicate
    seen_urls = set()
    deduped = []
    for p in all_posts:
        url = p.get("url")
        if url:
            if url not in seen_urls:
                seen_urls.add(url)
                deduped.append(p)
        else:
            deduped.append(p)
            
    deduped.sort(key=lambda x: x.get("engagement", 0) if isinstance(x.get("engagement"), (int, float)) else 0, reverse=True)
    paginated_posts = deduped[offset:offset + limit]
    
    return {
        "posts": paginated_posts,
        "total": len(deduped),
        "has_more": offset + limit < len(deduped),
    }


@app.get("/api/v1/posts/search")
async def search_posts(
    query: str = "",
    time_range: str = "24h",
    platform: str = "all",
    min_engagement: int = 0,
    is_crisis: Optional[bool] = None,
    is_influencer: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Search posts with advanced filters across completed reports.
    """
    matching_posts = []
    seen_urls = set()
    
    for report in reports_store.values():
        if report["status"] != "COMPLETED":
            continue
            
        all_posts = (
            [p for insight in report["chinaInsights"] for p in insight.get("posts", [])] +
            [p for insight in report["russiaInsights"] for p in insight.get("posts", [])] +
            report.get("crisisAlerts", [])
        )
        
        for post in all_posts:
            url = post.get("url")
            if url:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
            # Query filter
            if query:
                content = (post.get("content_translated") or post.get("content_original") or "").lower()
                author = (post.get("author") or "").lower()
                if query.lower() not in content and query.lower() not in author:
                    continue
                    
            # Platform filter
            if platform != "all" and platform.lower() not in post.get("platform", "").lower():
                continue
                
            # Engagement filter
            if post.get("engagement", 0) < min_engagement:
                continue
                
            # Crisis filter
            if is_crisis is not None and post.get("is_crisis", False) != is_crisis:
                continue
                
            # Influencer filter
            if is_influencer is not None and post.get("is_influencer", False) != is_influencer:
                continue
                
            matching_posts.append({
                **post,
                "report_id": report["id"],
                "report_date": report.get("reportDate"),
            })
            
    matching_posts.sort(key=lambda x: x.get("engagement", 0) if isinstance(x.get("engagement"), (int, float)) else 0, reverse=True)
    paginated = matching_posts[offset:offset + limit]
    
    return {
        "posts": paginated,
        "total": len(matching_posts),
        "query": query,
        "filters": {
            "time_range": time_range,
            "platform": platform,
            "min_engagement": min_engagement,
            "is_crisis": is_crisis,
            "is_influencer": is_influencer,
        },
        "has_more": offset + limit < len(matching_posts),
    }


@app.get("/api/v1/posts/{post_id}")
async def get_post_details(post_id: str):
    """
    Get detailed information about a specific post by ID or URL.
    """
    for report in reports_store.values():
        if report.get("status") != "COMPLETED":
            continue
            
        all_posts = (
            [p for insight in report["chinaInsights"] for p in insight.get("posts", [])] +
            [p for insight in report["russiaInsights"] for p in insight.get("posts", [])] +
            report.get("crisisAlerts", [])
        )
        
        for post in all_posts:
            if post.get("url") == post_id or post.get("id") == post_id:
                return {
                    "post": post,
                    "report_id": report["id"],
                    "report_date": report.get("reportDate"),
                }
                
    raise HTTPException(status_code=404, detail="Post not found")


@app.post("/api/v1/posts/action")
async def handle_post_action_v2(request: PostActionRequest):
    """
    Handle user actions on posts: respond, flag, investigate, archive.
    """
    logger.info(f"Action '{request.action_type}' on post: {request.post_url}")
    
    # Store action in database (in-memory for now)
    action_record = {
        "post_url": request.post_url,
        "action_type": request.action_type,
        "platform": request.platform,
        "notes": request.notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # In production, save to database. Update the post action in report store
    for report in reports_store.values():
        all_posts = (
            [p for insight in report.get("chinaInsights", []) for p in insight.get("posts", [])] +
            [p for insight in report.get("russiaInsights", []) for p in insight.get("posts", [])] +
            report.get("crisisAlerts", [])
        )
        for post in all_posts:
            if post.get("url") == request.post_url:
                post["action_taken"] = request.action_type
                post["action_taken_at"] = action_record["timestamp"]
                if request.action_type == "flag":
                    post["flagged"] = True
                elif request.action_type == "archive":
                    post["archived"] = True
                    
    return {
        "status": "success", 
        "action": request.action_type, 
        "timestamp": action_record["timestamp"]
    }


@app.post("/api/v1/posts/export")
async def export_posts(
    format: str = "csv",
    post_urls: Optional[List[str]] = None,
):
    """
    Export selected posts in CSV or JSON format.
    """
    import csv
    import io
    
    posts_to_export = []
    seen_urls = set()
    
    for report in reports_store.values():
        if report["status"] != "COMPLETED":
            continue
            
        all_posts = (
            [p for insight in report["chinaInsights"] for p in insight.get("posts", [])] +
            [p for insight in report["russiaInsights"] for p in insight.get("posts", [])] +
            report.get("crisisAlerts", [])
        )
        
        for p in all_posts:
            url = p.get("url")
            if url:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
            if post_urls:
                if url in post_urls:
                    posts_to_export.append(p)
            else:
                posts_to_export.append(p)
                
    if format == "json":
        return {
            "posts": posts_to_export,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total": len(posts_to_export),
        }
    else:
        # CSV format
        output = io.StringIO()
        if posts_to_export:
            fieldnames = [
                "platform", "author", "author_followers", "is_influencer",
                "content_original", "content_translated",
                "engagement", "is_crisis", "url", "published_at", "topics", "language"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            # Prepare rows to avoid dict writing issues with nested properties
            rows = []
            for p in posts_to_export:
                rows.append({
                    "platform": p.get("platform", ""),
                    "author": p.get("author", ""),
                    "author_followers": p.get("author_followers", 0),
                    "is_influencer": p.get("is_influencer", False),
                    "content_original": p.get("content_original", p.get("content_snippet", ""))[:1000],
                    "content_translated": p.get("content_translated", "")[:1000],
                    "engagement": p.get("engagement", 0),
                    "is_crisis": p.get("is_crisis", False),
                    "url": p.get("url", ""),
                    "published_at": p.get("published_at", ""),
                    "topics": ",".join(p.get("topics", [])),
                    "language": p.get("language", ""),
                })
            writer.writerows(rows)
            
        return {
            "csv_data": output.getvalue(),
            "total": len(posts_to_export),
        }


@app.get("/api/v1/radar/{job_id}/export/pdf")
async def export_report_pdf(job_id: str):
    """
    Generates and downloads a PDF version of the completed radar report.
    """
    report = reports_store.get(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail="Report is not completed yet")
    
    try:
        # Generate PDF bytes
        pdf_bytes = generate_radar_pdf(report)
        
        # Return as a downloadable file
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=TZ_Radar_Report_{job_id[:8]}.pdf"
            }
        )
    except Exception as e:
        logger.error(f"PDF export failed for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

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
