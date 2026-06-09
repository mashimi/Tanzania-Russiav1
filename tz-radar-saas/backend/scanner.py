"""Agent Reach orchestration layer — EXA REAL-TIME DATA.

Calls mcporter to query Exa MCP for actual web search results.
Parses the text output into structured SocialPost objects.
Analysis is heuristic (zero API cost) — detects crisis signals,
payment friction, visa queries, and flight discussion.
"""

import asyncio
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

# ── Keyword sets (mirrors agent_reach/diplomat_tracker.py) ─────────────

KEYWORDS_RU = [
    "Танзания инвестиции 2026",
    "прямые рейсы Танзания",
    "Танзания Самия Сулуху Хассан",
    "Занзибар бизнес делегация",
    "Танзания Россия экономика",
    "Танзания туризм партнёрство",
    "Занзибар инвестиции",
    "российские туристы Танзания",
    "Танзания виза новости",
    "Серенгети бизнес",
]

KEYWORDS_CN = [
    "坦桑尼亚 投资 机遇",
    "中坦 旅游 合作",
    "坦桑尼亚 总统 经济",
    "桑给巴尔 商务 考察",
    "坦桑尼亚 一带一路",
    "坦桑尼亚 签证 政策",
    "坦桑尼亚 直飞 航班",
    "坦桑尼亚 矿业 合作",
    "坦桑尼亚 农业 投资",
    "中坦 经贸 合作",
]

# ── Crisis / risk detection patterns ───────────────────────────────────

CRISIS_PATTERNS_RU = [
    r"проблем", r"мошен", r"опасн", r"грабёж", r"кража",
    r"обман", r"авария", r"теракт", r"болезн", r"маляр",
]
CRISIS_PATTERNS_CN = [
    "避坑", "疟疾", "宰客", "诈骗", "危险", "抢劫", "生病", "事故",
]

PAYMENT_PATTERNS_RU = [r"оплата", r"карта", r"деньги", r"перевод", r"валюта"]
VISA_PATTERNS_RU = [r"виза", r"документ", r"паспорт", r"разрешен"]
FLIGHT_PATTERNS_RU = [r"рейс", r"билет", r"авиа", r"чартер"]
FLIGHT_PATTERNS_CN = ["航班", "直飞", "机票", "包机"]

# ── Exa result parser ─────────────────────────────────────────────────

# Max per-keyword results to limit runtime
MAX_RESULTS_PER_KEYWORD = 3


def _get_mcporter_path() -> Optional[str]:
    """Get the full path to mcporter CLI.

    Returns None if not found. On Windows, mcporter is a .cmd file
    installed by npm to AppData/Roaming/npm/.
    """
    # Try explicit known paths first
    import os as _os
    npm_global = _os.path.expanduser("~\\AppData\\Roaming\\npm")
    win_mcporter = _os.path.join(npm_global, "mcporter.cmd")
    if _os.path.isfile(win_mcporter):
        return win_mcporter

    # Fall back to shutil.which
    mcporter = shutil.which("mcporter") or shutil.which("mcporter.cmd")
    if mcporter:
        return mcporter

    logger.warning("mcporter not found. Install: npm install -g mcporter")
    return None


def _check_mcporter() -> bool:
    """Check if mcporter CLI is available and Exa is configured."""
    mcporter = _get_mcporter_path()
    if not mcporter:
        return False
    try:
        r = subprocess.run(
            [mcporter, "config", "list"],
            capture_output=True, encoding="utf-8", errors="replace", timeout=5,
        )
        if "exa" not in r.stdout.lower():
            logger.warning("Exa not configured in mcporter. Run: mcporter config add exa https://mcp.exa.ai/mcp")
            return False
        return True
    except Exception as e:
        logger.error(f"mcporter check failed: {e}")
        return False


def _parse_exa_output(output: str) -> List[Dict[str, Any]]:
    """Parse Exa MCP text output into structured result dicts.

    Exa output format (per result):
        Title: ...
        URL: ...
        Published: ...
        Author: ...
        Highlights:
        [text content...]
        ---
    """
    results = []
    # Split on --- separator between results
    blocks = re.split(r"\n---\n", output.strip())
    for block in blocks:
        if not block.strip():
            continue
        title = ""
        url = ""
        published = ""
        author = ""
        # Extract highlights (text content)
        highlights = ""

        lines = block.split("\n")
        in_highlights = False
        highlight_lines = []

        for line in lines:
            if line.startswith("Title: "):
                title = line[7:].strip()
            elif line.startswith("URL: "):
                url = line[5:].strip()
            elif line.startswith("Published: "):
                published = line[11:].strip()
            elif line.startswith("Author: "):
                author = line[8:].strip()
            elif line.strip() == "Highlights:":
                in_highlights = True
            elif in_highlights:
                # Remove [...]
                cleaned = re.sub(r'\[\.\.\.\]', '', line).strip()
                if cleaned:
                    highlight_lines.append(cleaned)

        highlights = " ".join(highlight_lines)

        if title or highlights:
            results.append({
                "title": title,
                "url": url,
                "published": published,
                "author": author if author and author != "N/A" else "Unknown",
                "text": highlights[:500] if highlights else title,
            })

    return results


async def run_exa_search(keyword: str, num_results: int = MAX_RESULTS_PER_KEYWORD) -> str:
    """Run a single Exa search via mcporter CLI.

    Uses subprocess.run in a thread executor so it works on Windows
    where .cmd files require shell=True.
    """
    mcporter = _get_mcporter_path()
    if not mcporter:
        return ""
    cmd = [
        mcporter, "call",
        f"exa.web_search_exa(query: \"{keyword}\", numResults: {num_results})",
    ]
    logger.info(f"Exa search: {keyword}")

    def _run():
        return subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
        )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run)

    if result.returncode != 0:
        stderr_text = result.stderr.decode("utf-8", errors="replace")[:200]
        logger.error(f"Exa search failed for '{keyword}': {stderr_text}")
        return ""
    return result.stdout.decode("utf-8", errors="replace").strip()


def _detect_crisis(text: str, patterns: List[str]) -> bool:
    """Check if text contains any crisis pattern."""
    text_lower = text.lower()
    for p in patterns:
        try:
            if re.search(p, text_lower):
                return True
        except re.error:
            if p.lower() in text_lower:
                return True
    return False


def _detect_pattern(text: str, patterns: List[str]) -> bool:
    """Check if text contains any pattern."""
    text_lower = text.lower()
    for p in patterns:
        try:
            if re.search(p, text_lower):
                return True
        except re.error:
            if p.lower() in text_lower:
                return True
    return False


async def scan_russia_market(
    custom_keywords: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Scan Russian market via Exa MCP with real web data.

    Returns structured posts with crisis detection and topic categorization.
    """
    if not _check_mcporter():
        logger.warning("mcporter/Exa unavailable — Russia scan will return empty results")
        return []

    keywords = KEYWORDS_RU + (custom_keywords or [])
    # Deduplicate
    keywords = list(dict.fromkeys(keywords))
    all_posts = []

    for kw in keywords:
        output = await run_exa_search(kw)
        if not output:
            continue

        parsed = _parse_exa_output(output)
        for item in parsed:
            text = item.get("text", "")
            title = item.get("title", "")
            content = f"{title}: {text}"

            post = {
                "platform": "Exa (Russia/Semantic)",
                "author": item.get("author", "Unknown"),
                "content_snippet": content[:250],
                "engagement": 0,  # Exa doesn't return engagement metrics
                "is_crisis": _detect_crisis(content, CRISIS_PATTERNS_RU),
                "url": item.get("url", ""),
                "published": item.get("published", ""),
                "source_keyword": kw,
            }
            all_posts.append(post)

        # Rate limit respect
        await asyncio.sleep(0.5)

    return all_posts


async def scan_china_market(
    custom_keywords: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Scan Chinese market via Exa MCP.

    Exa supports semantic search across Chinese-language content.
    This provides real data from Chinese news, forums, and social mentions.
    """
    if not _check_mcporter():
        logger.warning("mcporter/Exa unavailable — China scan will return empty results")
        return []

    keywords = KEYWORDS_CN + (custom_keywords or [])
    keywords = list(dict.fromkeys(keywords))
    all_posts = []

    for kw in keywords:
        output = await run_exa_search(kw)
        if not output:
            continue

        parsed = _parse_exa_output(output)
        for item in parsed:
            text = item.get("text", "")
            title = item.get("title", "")
            content = f"{title}: {text}"

            post = {
                "platform": "Exa (China/Semantic)",
                "author": item.get("author", "Unknown"),
                "content_snippet": content[:250],
                "engagement": 0,
                "is_crisis": _detect_crisis(content, CRISIS_PATTERNS_CN),
                "url": item.get("url", ""),
                "published": item.get("published", ""),
                "source_keyword": kw,
            }
            all_posts.append(post)

        await asyncio.sleep(0.5)

    return all_posts


# ── Analysis functions (zero API cost, pure heuristic) ─────────────────


def _get_searchable_text(post: Dict[str, Any]) -> str:
    """Get the full searchable text from a post (title + snippet + text)."""
    parts = [
        post.get("title", ""),
        post.get("content_snippet", ""),
        post.get("text", ""),
    ]
    return " ".join(parts)


def analyze_russia_posts(posts: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """Analyze Russian posts for insights and crisis alerts.

    Returns (insights, crisis_alerts).
    """
    insights = []
    crisis_alerts = [p for p in posts if p.get("is_crisis")]

    if not posts:
        return insights, crisis_alerts

    # Check for payment friction topics
    payment_posts = [
        p for p in posts
        if _detect_pattern(p.get("content_snippet", ""), PAYMENT_PATTERNS_RU)
    ]
    if payment_posts:
        insights.append({
            "trend": "Payment Friction / Валюта и оплата",
            "sentiment": "Negative",
            "action": "Highlight UnionPay, M-Pesa, and crypto payment options on Russian-language booking pages. Add FAQ about card acceptance in Tanzania.",
            "posts": [{
                "platform": p["platform"],
                "author": p["author"],
                "content_snippet": p["content_snippet"][:200],
                "engagement": 0,
                "is_crisis": p.get("is_crisis", False),
            } for p in payment_posts[:2]],
        })

    # Check for visa/document queries
    visa_posts = [
        p for p in posts
        if _detect_pattern(p.get("content_snippet", ""), VISA_PATTERNS_RU)
    ]
    if visa_posts:
        insights.append({
            "trend": "Visa & Entry Requirements / Виза",
            "sentiment": "Neutral",
            "action": "Publish a clear visa-on-arrival guide in Russian. Post step-by-step on Russian travel forums.",
            "posts": [{
                "platform": p["platform"],
                "author": p["author"],
                "content_snippet": p["content_snippet"][:200],
                "engagement": 0,
                "is_crisis": p.get("is_crisis", False),
            } for p in visa_posts[:2]],
        })

    # Check for flight/aviation discussion
    flight_posts = [
        p for p in posts
        if _detect_pattern(p.get("content_snippet", ""), FLIGHT_PATTERNS_RU)
    ]
    if flight_posts:
        insights.append({
            "trend": "Flights & Logistics / Авиабилеты (BREAKING: direct flights from July 2!)",
            "sentiment": "Positive",
            "action": "Update your website immediately to promote new Air Tanzania direct flights from Moscow (starting July 2). Create 'Moscow → Zanzibar → Serengeti' packages.",
            "posts": [{
                "platform": p["platform"],
                "author": p["author"],
                "content_snippet": p["content_snippet"][:200],
                "engagement": 0,
                "is_crisis": p.get("is_crisis", False),
            } for p in flight_posts[:2]],
        })

    # General investment/tourism interest
    investment_posts = [
        p for p in posts
        if any(kw in p.get("content_snippet", "") for kw in ["инвестиц", "экономик", "партнёр"])
    ]
    if investment_posts and len(investment_posts) >= 2:
        insights.append({
            "trend": "Investment & Economic Partnership / Инвестиции",
            "sentiment": "Positive",
            "action": "Tanzania targets 500K Russian tourists by 2030. Prepare Russian-language B2B materials for TIC (Tanzania Investment Centre). Attend Russia-Africa forums.",
            "posts": [{
                "platform": p["platform"],
                "author": p["author"],
                "content_snippet": p["content_snippet"][:200],
                "engagement": 0,
                "is_crisis": p.get("is_crisis", False),
            } for p in investment_posts[:2]],
        })

    return insights, crisis_alerts


def analyze_china_posts(posts: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """Analyze Chinese posts for insights and crisis alerts."""
    insights = []
    crisis_alerts = [p for p in posts if p.get("is_crisis")]

    if not posts:
        return insights, crisis_alerts

    # Check for flight/aviation
    flight_cn = [
        p for p in posts
        if _detect_pattern(p.get("content_snippet", ""), FLIGHT_PATTERNS_CN)
    ]
    if flight_cn:
        insights.append({
            "trend": "航班信息 / Direct Flight Discussion",
            "sentiment": "Positive",
            "action": "Publish Chinese-language content about new flight connections to Tanzania. Emphasize convenience and frequency.",
            "posts": [{
                "platform": p["platform"],
                "author": p["author"],
                "content_snippet": p["content_snippet"][:200],
                "engagement": 0,
                "is_crisis": p.get("is_crisis", False),
            } for p in flight_cn[:2]],
        })

    # Investment interest
    invest_cn = [
        p for p in posts
        if any(kw in p.get("content_snippet", "") for kw in ["投资", "合作", "经贸", "一带一路"])
    ]
    if invest_cn:
        insights.append({
            "trend": "投资与合作 / Belt & Road Investment",
            "sentiment": "Positive",
            "action": "Publish Mandarin case studies on WeChat Official Accounts. Attend China-Africa forums. Highlight Tanzania's Belt & Road projects.",
            "posts": [{
                "platform": p["platform"],
                "author": p["author"],
                "content_snippet": p["content_snippet"][:200],
                "engagement": 0,
                "is_crisis": p.get("is_crisis", False),
            } for p in invest_cn[:2]],
        })

    # Visa policy queries
    visa_cn = [
        p for p in posts
        if any(kw in p.get("content_snippet", "") for kw in ["签证", "政策", "入境"])
    ]
    if visa_cn:
        insights.append({
            "trend": "签证政策 / Visa Policy Queries",
            "sentiment": "Neutral",
            "action": "Ensure visa-on-arrival information is prominently displayed on Chinese social media (Weibo, XiaoHongShu). Create a simple infographic.",
            "posts": [{
                "platform": p["platform"],
                "author": p["author"],
                "content_snippet": p["content_snippet"][:200],
                "engagement": 0,
                "is_crisis": p.get("is_crisis", False),
            } for p in visa_cn[:2]],
        })

    return insights, crisis_alerts


def build_executive_summary(
    ru_posts: List[Dict], cn_posts: List[Dict],
    ru_insights: List[Dict], cn_insights: List[Dict],
    crisis_alerts: List[Dict],
) -> str:
    """Build a human-readable executive summary from scan results."""
    total = len(ru_posts) + len(cn_posts)
    crisis_count = len(crisis_alerts)

    # Count recent articles (published within last 30 days)
    recent_count = 0
    for p in ru_posts + cn_posts:
        pub = p.get("published", "")
        if pub:
            try:
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - dt).days <= 30:
                    recent_count += 1
            except (ValueError, TypeError):
                pass

    parts = [
        f"Radar scan complete. {total} articles collected across "
        f"Russian and Chinese markets. {recent_count} published within the last 30 days."
    ]

    if crisis_count > 0:
        parts.append(
            f"⚠️ {crisis_count} crisis signal(s) detected requiring attention."
        )

    if ru_insights:
        trends = ", ".join(i["trend"].split("/")[0].strip() for i in ru_insights[:3])
        parts.append(f"Russia: {trends}.")

    if cn_insights:
        trends = ", ".join(i["trend"].split("/")[0].strip() for i in cn_insights[:3])
        parts.append(f"China: {trends}.")

    if not ru_insights and not cn_insights:
        parts.append("No significant new trends detected beyond baseline.")

    return " ".join(parts)


def build_pdf_report_text(
    ru_insights: List[Dict], cn_insights: List[Dict],
    crisis_alerts: List[Dict], executive_summary: str,
) -> str:
    """Generate the 1-page 'Diplomatic Dividend' special report text."""
    lines = []
    lines.append("=" * 62)
    lines.append("  THE DIPLOMATIC DIVIDEND — SPECIAL REPORT")
    lines.append("  What Russia & China Are Saying About Tanzania This Week")
    lines.append("=" * 62)
    lines.append(f"  Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}")
    lines.append("")

    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 62)
    lines.append(f"  {executive_summary}")
    lines.append("")

    if crisis_alerts:
        lines.append("⚠ CRISIS ALERTS")
        lines.append("-" * 62)
        for a in crisis_alerts[:3]:
            lines.append(f"  • [{a.get('platform','?')}] {a.get('content_snippet','')[:120]}")
        lines.append("")

    lines.append("KEY INSIGHTS")
    lines.append("-" * 62)
    for market, insights in [("RUSSIA", ru_insights), ("CHINA", cn_insights)]:
        if insights:
            lines.append(f"\n  🇷🇺 {market}" if market == "RUSSIA" else f"\n  🇨🇳 {market}")
            for i in insights:
                lines.append(f"    Trend: {i['trend']}")
                lines.append(f"    Sentiment: {i['sentiment']}")
                lines.append(f"    Action: {i['action'][:100]}...")
    lines.append("")

    lines.append("STRATEGIC RECOMMENDATIONS")
    lines.append("-" * 62)
    for market, insights in [("Russia", ru_insights), ("China", cn_insights)]:
        for i in insights[:2]:
            lines.append(f"  • {market}: {i['action'][:150]}")
    lines.append("")
    lines.append("-" * 62)
    lines.append("Powered by Agent Reach — Geopolitical Tourism Radar")
    lines.append("-" * 62)
    return "\n".join(lines)