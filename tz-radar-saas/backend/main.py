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

from models import ScanRequest, ScanTriggerResponse
# Import the new unified, concurrent, AI-translated scanner
from scanner import run_full_scan_and_translate


# ── In-memory store (swap for Prisma/PostgreSQL in production) ──
reports_store: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 TZ Tourism Radar API starting up (Enhanced Translation Engine)...")
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