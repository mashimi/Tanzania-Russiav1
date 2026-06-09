"""FastAPI entrypoint for the TZ Tourism Radar SaaS backend.

Non-blocking architecture:
  - POST /api/v1/radar/trigger  → spawns background scan, returns job_id
  - GET  /api/v1/radar/{job_id}  → returns completed report
  - Frontend polls GET endpoint every 3s until status == COMPLETED
"""

import uuid
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from models import ScanRequest, ScanTriggerResponse
from scanner import scan_china_market, scan_russia_market


# ── In-memory store (swap for Prisma/PostgreSQL in production) ──
reports_store: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TZ Tourism Radar API starting up...")
    yield
    logger.info("TZ Tourism Radar API shutting down...")


app = FastAPI(
    title="TZ Tourism Radar API",
    description="Geopolitical Intelligence for Tanzanian Tourism — monitors China & Russia markets.",
    version="1.0.0",
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
    return {"status": "ok", "service": "tz-radar-api"}


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
        "executiveSummary": "Processing...",
        "chinaInsights": [],
        "russiaInsights": [],
        "crisisAlerts": [],
        "reportDate": None,
    }

    background_tasks.add_task(
        run_full_scan, job_id, request.client_id, request.custom_keywords
    )
    return {"job_id": job_id, "status": "processing"}


async def run_full_scan(
    job_id: str, client_id: str, custom_keywords: List[str]
):
    """Background task: execute Agent Reach scanners, analyze, save results."""
    try:
        logger.info(f"Starting scan for job {job_id}")

        # 1. Define keyword sets (default + client custom)
        cn_keywords = [
            "坦桑尼亚 游猎",
            "桑给巴尔 酒店",
            "坦桑尼亚 签证 政策",
        ] + (custom_keywords or [])

        ru_keywords = [
            "Занзибар отдых",
            "Танзания сафари",
            "Танзания туризм 2026",
        ] + (custom_keywords or [])

        # 2. Execute scans in parallel
        import asyncio
        cn_posts, ru_posts = await asyncio.gather(
            scan_china_market(cn_keywords),
            scan_russia_market(ru_keywords),
        )

        # 3. Heuristic analysis (zero API cost)
        cn_insights = []
        crisis_posts_cn = [p for p in cn_posts if p["is_crisis"]]
        if crisis_posts_cn:
            cn_insights.append({
                "trend": "游客体验 / 安全问题",
                "sentiment": "Negative",
                "action": "更新中文网站安全 FAQ，重点说明疟疾预防和旅行保险",
                "posts": crisis_posts_cn[:2],
            })

        high_engagement_cn = sorted(cn_posts, key=lambda p: p["engagement"], reverse=True)[:3]
        if high_engagement_cn:
            cn_insights.append({
                "trend": "热门推荐 — 高互动内容",
                "sentiment": "Positive",
                "action": "联系这些 KOL 进行合作推广",
                "posts": high_engagement_cn[:2],
            })

        ru_insights = []
        payment_posts = [
            p for p in ru_posts
            if any(k in p["content_snippet"].lower() for k in ["оплата", "карта", "деньги"])
        ]
        if payment_posts:
            ru_insights.append({
                "trend": "Payment Friction (оплата/карта)",
                "sentiment": "Negative",
                "action": "Highlight UnionPay / Crypto payment options on Russian landing pages",
                "posts": payment_posts[:2],
            })

        visa_posts = [
            p for p in ru_posts
            if any(k in p["content_snippet"].lower() for k in ["виза", "документ", "паспорт"])
        ]
        if visa_posts:
            ru_insights.append({
                "trend": "Visa & Documentation Queries (виза/документы)",
                "sentiment": "Neutral",
                "action": "Publish clear visa-on-arrival guide in Russian on your website",
                "posts": visa_posts[:2],
            })

        crisis_alerts = crisis_posts_cn + [
            p for p in ru_posts if p["is_crisis"]
        ]

        # Build executive summary
        total_posts = len(cn_posts) + len(ru_posts)
        crisis_count = len(crisis_alerts)
        if crisis_count > 0:
            summary = (
                f"Scan complete. {total_posts} posts collected across China & Russia markets. "
                f"{crisis_count} crisis flag(s) detected requiring attention. "
                f"China: {cn_insights[0]['trend'] if cn_insights else 'No significant trends'}. "
                f"Russia: {ru_insights[0]['trend'] if ru_insights else 'No significant trends'}."
            )
        else:
            summary = (
                f"Scan complete. {total_posts} posts collected. "
                f"No immediate crisis signals. China market: {len(cn_insights)} insight(s). "
                f"Russia market: {len(ru_insights)} insight(s). "
                f"Market sentiment is stable."
            )

        # 4. Save to store
        reports_store[job_id] = {
            "id": job_id,
            "clientId": client_id,
            "status": "COMPLETED",
            "executiveSummary": summary,
            "chinaInsights": cn_insights,
            "russiaInsights": ru_insights,
            "crisisAlerts": crisis_alerts,
            "reportDate": __import__("datetime").datetime.utcnow().isoformat(),
        }
        logger.success(f"Scan {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Scan {job_id} failed: {e}")
        reports_store[job_id] = {
            "id": job_id,
            "clientId": client_id,
            "status": "FAILED",
            "executiveSummary": f"Scan failed: {str(e)}",
            "chinaInsights": [],
            "russiaInsights": [],
            "crisisAlerts": [],
            "reportDate": __import__("datetime").datetime.utcnow().isoformat(),
        }


@app.get("/api/v1/radar/{job_id}")
async def get_report(job_id: str):
    """Poll this endpoint to retrieve a completed radar report."""
    report = reports_store.get(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/api/v1/radar")
async def list_reports(client_id: str = ""):
    """List all reports, optionally filtered by client_id."""
    reports = list(reports_store.values())
    if client_id:
        reports = [r for r in reports if r["clientId"] == client_id]
    return {
        "reports": sorted(reports, key=lambda r: r.get("reportDate", ""), reverse=True),
        "total": len(reports),
    }