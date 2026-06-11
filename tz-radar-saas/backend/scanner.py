"""Agent Reach orchestration layer -- EXA REAL-TIME DATA.

Calls mcporter to query Exa MCP for actual web search results.
Parses the text output into structured SocialPost objects.
Analysis is heuristic (zero API cost) -- detects crisis signals,
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

# -- Expanded Categorized Keyword Matrices ----------------------------

KEYWORD_MATRIX_CN: Dict[str, List[str]] = {
    "tourism": [
        "\u5766\u6851\u5c3c\u4e9a \u65c5\u6e38\u653b\u7565",
        "\u6851\u7ed9\u5df4\u5c14 \u9152\u5e97 \u63a8\u8350",
        "\u5766\u6851\u5c3c\u4e9a \u6e38\u730e \u907f\u5751",
        "\u5766\u6851\u5c3c\u4e9a \u585e\u4f26\u76d6\u8482 \u52a8\u7269\u5927\u8fc1\u5f99",
        "\u5766\u6851\u5c3c\u4e9a \u4e3e\u529b\u9a6c\u624e\u7f57 \u767b\u5c71",
        "\u5766\u6851\u5c3c\u4e9a \u4e2d\u6587\u5bfc\u6e38",
        "\u5766\u6851\u5c3c\u4e9a \u65c5\u6e38 \u5b89\u5168",
    ],
    "investment": [
        "\u5766\u6851\u5c3c\u4e9a \u6295\u8d44 \u673a\u9047",
        "\u4e2d\u5766 \u65c5\u6e38 \u5408\u4f5c",
        "\u5766\u6851\u5c3c\u4e9a \u603b\u7edf \u7ecf\u6d4e",
        "\u6851\u7ed9\u5df4\u5c14 \u5546\u52a1 \u8003\u5bdf",
        "\u5766\u6851\u5c3c\u4e9a \u4e00\u5e26\u4e00\u8def",
        "\u5766\u6851\u5c3c\u4e9a \u77ff\u4e1a \u5408\u4f5c",
        "\u5766\u6851\u5c3c\u4e9a \u519c\u4e1a \u6295\u8d44",
        "\u4e2d\u5766 \u7ecf\u8d38 \u5408\u4f5c",
        "\u5766\u6851\u5c3c\u4e9a \u623f\u5730\u4ea7 \u6295\u8d44",
        "\u8fbe\u7d2f\u65af\u8428\u62c9\u59c6 \u6e2f\u53e3",
    ],
    "logistics": [
        "\u5766\u6851\u5c3c\u4e9a \u7b7e\u8bc1 \u653f\u7b56",
        "\u5766\u6851\u5c3c\u4e9a \u76f4\u98de \u822a\u73ed",
        "\u5766\u6851\u5c3c\u4e9a \u673a\u7968 \u4ef7\u683c",
        "\u5766\u6851\u5c3c\u4e9a \u5766\u8d5e\u94c1\u8def",
    ],
    "luxury": [
        "\u6851\u7ed9\u5df4\u5c14 \u5962\u534e \u5ea6\u5047\u6751",
        "\u5766\u6851\u5c3c\u4e9a \u9ad8\u7aef \u5b9a\u5236 \u6e38",
        "\u585e\u4f26\u76d6\u8482 \u8c6a\u534e \u5e10\u7bf7",
    ]
}

KEYWORD_MATRIX_RU: Dict[str, List[str]] = {
    "tourism": [
        "\u0417\u0430\u043d\u0437\u0438\u0431\u0430\u0440 \u043e\u0442\u0434\u044b\u0445 2026",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0441\u0430\u0444\u0430\u0440\u0438 \u043e\u0442\u0437\u044b\u0432\u044b",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0442\u0443\u0440\u0438\u0437\u043c \u0432\u0441\u0435 \u0432\u043a\u043b\u044e\u0447\u0435\u043d\u043e",
        "\u0440\u043e\u0441\u0441\u0438\u0439\u0441\u043a\u0438\u0435 \u0442\u0443\u0440\u0438\u0441\u0442\u044b \u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0432\u0438\u0437\u0430 \u043d\u043e\u0432\u043e\u0441\u0442\u0438",
    ],
    "investment": [
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0438\u043d\u0432\u0435\u0441\u0442\u0438\u0446\u0438\u0438 2026",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0421\u0430\u043c\u0438\u044f \u0421\u0443\u043b\u0443\u0445\u0443 \u0425\u0430\u0441\u0441\u0430\u043d",
        "\u0417\u0430\u043d\u0437\u0438\u0431\u0430\u0440 \u0431\u0438\u0437\u043d\u0435\u0441 \u0434\u0435\u043b\u0435\u0433\u0430\u0446\u0438\u044f",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0420\u043e\u0441\u0441\u0438\u044f \u044d\u043a\u043e\u043d\u043e\u043c\u0438\u043a\u0430",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0442\u0443\u0440\u0438\u0437\u043c \u043f\u0430\u0440\u0442\u043d\u0451\u0440\u0441\u0442\u0432\u043e",
        "\u0417\u0430\u043d\u0437\u0438\u0431\u0430\u0440 \u0438\u043d\u0432\u0435\u0441\u0442\u0438\u0446\u0438\u0438",
        "\u0414\u0430\u0440-\u044d\u0441-\u0421\u0430\u043b\u0430\u043c \u0434\u0435\u043b\u043e\u0432\u0430\u044f \u043c\u0438\u0441\u0441\u0438\u044f",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0434\u043e\u0431\u044b\u0447\u0430 \u0437\u043e\u043b\u043e\u0442\u0430",
    ],
    "logistics": [
        "\u043f\u0440\u044f\u043c\u044b\u0435 \u0440\u0435\u0439\u0441\u044b \u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u043f\u0435\u0440\u0435\u043b\u0435\u0442 \u0438\u0437 \u041c\u043e\u0441\u043a\u0432\u044b",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u0430 \u043a\u0430\u0440\u0442\u043e\u0439",
    ],
    "luxury": [
        "\u0440\u043e\u0441\u043a\u043e\u0448\u043d\u044b\u0435 \u043e\u0442\u0435\u043b\u0438 \u0417\u0430\u043d\u0437\u0438\u0431\u0430\u0440",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f VIP \u0442\u0443\u0440",
        "\u0421\u0435\u0440\u0435\u043d\u0433\u0435\u0442\u0438 \u043b\u044e\u043a\u0441 \u0441\u0430\u0444\u0430\u0440\u0438",
    ]
}


def get_all_keywords(
    matrix: Dict[str, List[str]],
    custom_keywords: Optional[List[str]] = None,
) -> List[str]:
    """Flatten the categorized matrix and deduplicate, adding client custom keywords."""
    flat_list: List[str] = []
    for category in matrix.values():
        flat_list.extend(category)
    if custom_keywords:
        flat_list.extend(custom_keywords)
    return list(dict.fromkeys(flat_list))

# -- Crisis / risk detection patterns --------------------------------

CRISIS_PATTERNS_RU: List[str] = [
    r"\u043f\u0440\u043e\u0431\u043b\u0435\u043c",
    r"\u043c\u043e\u0448\u0435\u043d",
    r"\u043e\u043f\u0430\u0441\u043d",
    r"\u0433\u0440\u0430\u0431\u0451\u0436",
    r"\u043a\u0440\u0430\u0436\u0430",
    r"\u043e\u0431\u043c\u0430\u043d",
    r"\u0430\u0432\u0430\u0440\u0438\u044f",
    r"\u0442\u0435\u0440\u0430\u043a\u0442",
    r"\u0431\u043e\u043b\u0435\u0437\u043d",
    r"\u043c\u0430\u043b\u044f\u0440",
]
CRISIS_PATTERNS_CN: List[str] = [
    "\u907f\u5751",
    "\u759f\u75be",
    "\u5bb0\u5ba2",
    "\u8bc8\u9a97",
    "\u5371\u9669",
    "\u62a2\u52ab",
    "\u751f\u75c5",
    "\u4e8b\u6545",
]

PAYMENT_PATTERNS_RU: List[str] = [r"\u043e\u043f\u043b\u0430\u0442\u0430", r"\u043a\u0430\u0440\u0442\u0430", r"\u0434\u0435\u043d\u044c\u0433\u0438", r"\u043f\u0435\u0440\u0435\u0432\u043e\u0434", r"\u0432\u0430\u043b\u044e\u0442\u0430"]
VISA_PATTERNS_RU: List[str] = [r"\u0432\u0438\u0437\u0430", r"\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442", r"\u043f\u0430\u0441\u043f\u043e\u0440\u0442", r"\u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d"]
FLIGHT_PATTERNS_RU: List[str] = [r"\u0440\u0435\u0439\u0441", r"\u0431\u0438\u043b\u0435\u0442", r"\u0430\u0432\u0438\u0430", r"\u0447\u0430\u0440\u0442\u0435\u0440"]
FLIGHT_PATTERNS_CN: List[str] = [
    "\u822a\u73ed",
    "\u76f4\u98de",
    "\u673a\u7968",
    "\u5305\u673a",
]

# Max per-keyword results to limit runtime
MAX_RESULTS_PER_KEYWORD: int = 3

# Cache the mcporter config probe so concurrent scans don't repeat it.
_MCPORTER_CHECK_CACHE: Optional[bool] = None


def _get_mcporter_path() -> Optional[str]:
    """Get the full path to mcporter CLI.

    Returns None if not found. On Windows, mcporter is a .cmd file
    installed by npm to AppData/Roaming/npm/.
    """
    import os as _os

    npm_global = _os.path.expanduser("~\\AppData\\Roaming\\npm")
    win_mcporter = _os.path.join(npm_global, "mcporter.cmd")
    if _os.path.isfile(win_mcporter):
        return win_mcporter

    mcporter = shutil.which("mcporter") or shutil.which("mcporter.cmd")
    if mcporter:
        return mcporter

    logger.warning("mcporter not found. Install: npm install -g mcporter")
    return None


def _check_mcporter() -> bool:
    """Pre-flight check for mcporter Exa availability (cached, best-effort).

    The old implementation returned False whenever ``mcporter config list``
    timed out, causing China scans to exit before attempting ``mcporter call``.
    """
    global _MCPORTER_CHECK_CACHE
    if _MCPORTER_CHECK_CACHE is not None:
        return _MCPORTER_CHECK_CACHE

    mcporter = _get_mcporter_path()
    if not mcporter:
        _MCPORTER_CHECK_CACHE = False
        return False

    shell = mcporter.lower().endswith(".cmd")
    try:
        r = subprocess.run(
            [mcporter, "config", "list"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            shell=shell,
        )
        ok = "exa" in r.stdout.lower()
        if not ok:
            logger.info(
                "Exa not reported by mcporter config list; "
                "direct searches will still be attempted."
            )
        _MCPORTER_CHECK_CACHE = ok
        return ok
    except Exception as e:
        logger.info(
            f"mcporter config preflight did not complete ({e}); "
            "direct searches will still be attempted."
        )
        _MCPORTER_CHECK_CACHE = False
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
    results: List[Dict[str, Any]] = []
    blocks = re.split(r"\n---\n", output.strip())
    for block in blocks:
        if not block.strip():
            continue
        title = ""
        url = ""
        published = ""
        author = ""
        highlights = ""

        lines = block.split("\n")
        in_highlights = False
        highlight_lines: List[str] = []

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
                cleaned = re.sub(r"\[\.\.\.\]", "", line).strip()
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


async def run_exa_search(
    keyword: str, num_results: int = MAX_RESULTS_PER_KEYWORD
) -> str:
    """Run a single Exa search via mcporter CLI.

    Uses subprocess.run in a thread executor. On Windows the .cmd file
    requires shell=True.  A 45-second timeout prevents one slow keyword
    from hanging the whole scan.
    """
    mcporter = _get_mcporter_path()
    if not mcporter:
        return ""
    cmd = [
        mcporter,
        "call",
        f"exa.web_search_exa(query: \"{keyword}\", numResults: {num_results})",
    ]
    logger.info(f"Exa search: {keyword}")

    def _run() -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
            shell=mcporter.lower().endswith(".cmd"),
        )

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, _run)
    except subprocess.TimeoutExpired:
        logger.warning(
            f"Exa search timed out for '{keyword}' after 45s; "
            "skipping this keyword."
        )
        return ""

    if result.returncode != 0:
        stderr_text = result.stderr[:200]
        logger.error(f"Exa search failed for '{keyword}': {stderr_text}")
        return ""
    return result.stdout.strip()


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


# ------------------------------------------------------------------
# Market scanning
# ------------------------------------------------------------------


async def scan_russia_market(
    custom_keywords: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Scan Russian market via Exa MCP with expanded keyword matrix."""
    _check_mcporter()  # best-effort preflight

    keywords = get_all_keywords(KEYWORD_MATRIX_RU, custom_keywords)
    all_posts: List[Dict[str, Any]] = []

    for kw in keywords:
        output = await run_exa_search(kw, num_results=3)
        if not output:
            continue

        parsed = _parse_exa_output(output)
        for item in parsed:
            text = item.get("text", "")
            title = item.get("title", "")
            content = f"{title}: {text}"

            post: Dict[str, Any] = {
                "platform": "Exa (Russia/Semantic)",
                "author": item.get("author", "Unknown"),
                "content_snippet": content[:250],
                "engagement": 0,
                "is_crisis": _detect_crisis(content, CRISIS_PATTERNS_RU),
                "url": item.get("url", ""),
                "published": item.get("published", ""),
                "source_keyword": kw,
            }
            all_posts.append(post)

        await asyncio.sleep(0.3)

    return all_posts


async def scan_china_market(
    custom_keywords: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Scan Chinese market via Exa MCP with expanded keyword matrix."""
    _check_mcporter()  # best-effort preflight

    keywords = get_all_keywords(KEYWORD_MATRIX_CN, custom_keywords)
    all_posts: List[Dict[str, Any]] = []

    for kw in keywords:
        output = await run_exa_search(kw, num_results=3)
        if not output:
            continue

        parsed = _parse_exa_output(output)
        for item in parsed:
            text = item.get("text", "")
            title = item.get("title", "")
            content = f"{title}: {text}"

            post: Dict[str, Any] = {
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

        await asyncio.sleep(0.3)

    return all_posts


# ------------------------------------------------------------------
# Heuristic analysis (zero API cost)
# ------------------------------------------------------------------


def _get_searchable_text(post: Dict[str, Any]) -> str:
    """Get the full searchable text from a post (title + snippet + text)."""
    parts = [
        post.get("title", ""),
        post.get("content_snippet", ""),
        post.get("text", ""),
    ]
    return " ".join(parts)


def analyze_russia_posts(
    posts: List[Dict[str, Any]],
) -> Tuple[List[Dict], List[Dict]]:
    """Analyze Russian posts for insights and crisis alerts.

    Returns (insights, crisis_alerts).
    """
    insights: List[Dict] = []
    crisis_alerts = [p for p in posts if p.get("is_crisis")]

    if not posts:
        return insights, crisis_alerts

    # Payment friction
    payment_posts = [
        p
        for p in posts
        if _detect_pattern(p.get("content_snippet", ""), PAYMENT_PATTERNS_RU)
    ]
    if payment_posts:
        insights.append({
            "trend": "Payment Friction / Valyuta i oplata",
            "sentiment": "Negative",
            "action": (
                "Highlight UnionPay, M-Pesa, and crypto payment options on "
                "Russian-language booking pages. Add FAQ about card acceptance "
                "in Tanzania."
            ),
            "posts": [
                {
                    "platform": p["platform"],
                    "author": p["author"],
                    "content_snippet": p["content_snippet"][:200],
                    "engagement": 0,
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in payment_posts[:2]
            ],
        })

    # Visa / document queries
    visa_posts = [
        p
        for p in posts
        if _detect_pattern(p.get("content_snippet", ""), VISA_PATTERNS_RU)
    ]
    if visa_posts:
        insights.append({
            "trend": "Visa & Entry Requirements / Viza",
            "sentiment": "Neutral",
            "action": (
                "Publish a clear visa-on-arrival guide in Russian. "
                "Post step-by-step on Russian travel forums."
            ),
            "posts": [
                {
                    "platform": p["platform"],
                    "author": p["author"],
                    "content_snippet": p["content_snippet"][:200],
                    "engagement": 0,
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in visa_posts[:2]
            ],
        })

    # Flight / aviation
    flight_posts = [
        p
        for p in posts
        if _detect_pattern(p.get("content_snippet", ""), FLIGHT_PATTERNS_RU)
    ]
    if flight_posts:
        insights.append({
            "trend": (
                "Flights & Logistics / Aviabilety "
                "(BREAKING: direct flights from July 2!)"
            ),
            "sentiment": "Positive",
            "action": (
                "Update your website immediately to promote new Air Tanzania "
                "direct flights from Moscow (starting July 2). Create "
                "'Moscow -> Zanzibar -> Serengeti' packages."
            ),
            "posts": [
                {
                    "platform": p["platform"],
                    "author": p["author"],
                    "content_snippet": p["content_snippet"][:200],
                    "engagement": 0,
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in flight_posts[:2]
            ],
        })

    # Investment / economic partnership
    investment_posts = [
        p
        for p in posts
        if any(
            kw in p.get("content_snippet", "")
            for kw in ["investits", "ekonomik", "partnyor"]
        )
    ]
    if investment_posts and len(investment_posts) >= 2:
        insights.append({
            "trend": "Investment & Economic Partnership / Investitsii",
            "sentiment": "Positive",
            "action": (
                "Tanzania targets 500K Russian tourists by 2030. Prepare "
                "Russian-language B2B materials for TIC (Tanzania Investment "
                "Centre). Attend Russia-Africa forums."
            ),
            "posts": [
                {
                    "platform": p["platform"],
                    "author": p["author"],
                    "content_snippet": p["content_snippet"][:200],
                    "engagement": 0,
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in investment_posts[:2]
            ],
        })

    return insights, crisis_alerts


def analyze_china_posts(
    posts: List[Dict[str, Any]],
) -> Tuple[List[Dict], List[Dict]]:
    """Analyze Chinese posts for insights and crisis alerts."""
    insights: List[Dict] = []
    crisis_alerts = [p for p in posts if p.get("is_crisis")]

    if not posts:
        return insights, crisis_alerts

    # Flight / aviation
    flight_cn = [
        p
        for p in posts
        if _detect_pattern(p.get("content_snippet", ""), FLIGHT_PATTERNS_CN)
    ]
    if flight_cn:
        insights.append({
            "trend": "Direct Flight Discussion",
            "sentiment": "Positive",
            "action": (
                "Publish Chinese-language content about new flight "
                "connections to Tanzania. Emphasize convenience and frequency."
            ),
            "posts": [
                {
                    "platform": p["platform"],
                    "author": p["author"],
                    "content_snippet": p["content_snippet"][:200],
                    "engagement": 0,
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in flight_cn[:2]
            ],
        })

    # Investment interest
    invest_cn = [
        p
        for p in posts
        if any(
            kw in p.get("content_snippet", "")
            for kw in ["investment", "cooperation", "trade"]
        )
    ]
    if invest_cn:
        insights.append({
            "trend": "Belt & Road Investment",
            "sentiment": "Positive",
            "action": (
                "Publish Mandarin case studies on WeChat Official Accounts. "
                "Attend China-Africa forums. Highlight Tanzania's Belt & "
                "Road projects."
            ),
            "posts": [
                {
                    "platform": p["platform"],
                    "author": p["author"],
                    "content_snippet": p["content_snippet"][:200],
                    "engagement": 0,
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in invest_cn[:2]
            ],
        })

    # Visa policy queries
    visa_cn = [
        p
        for p in posts
        if any(
            kw in p.get("content_snippet", "")
            for kw in ["visa", "policy", "entry"]
        )
    ]
    if visa_cn:
        insights.append({
            "trend": "Visa Policy Queries",
            "sentiment": "Neutral",
            "action": (
                "Ensure visa-on-arrival information is prominently displayed "
                "on Chinese social media (Weibo, XiaoHongShu). Create a "
                "simple infographic."
            ),
            "posts": [
                {
                    "platform": p["platform"],
                    "author": p["author"],
                    "content_snippet": p["content_snippet"][:200],
                    "engagement": 0,
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in visa_cn[:2]
            ],
        })

    return insights, crisis_alerts


def build_executive_summary(
    ru_posts: List[Dict],
    cn_posts: List[Dict],
    ru_insights: List[Dict],
    cn_insights: List[Dict],
    crisis_alerts: List[Dict],
) -> str:
    """Build a human-readable executive summary from scan results."""
    total = len(ru_posts) + len(cn_posts)
    crisis_count = len(crisis_alerts)

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
        f"Russian and Chinese markets. {recent_count} published within "
        "the last 30 days."
    ]

    if crisis_count > 0:
        parts.append(
            f"{crisis_count} crisis signal(s) detected requiring attention."
        )

    if ru_insights:
        trends = ", ".join(
            i["trend"].split("/")[0].strip() for i in ru_insights[:3]
        )
        parts.append(f"Russia: {trends}.")

    if cn_insights:
        trends = ", ".join(
            i["trend"].split("/")[0].strip() for i in cn_insights[:3]
        )
        parts.append(f"China: {trends}.")

    if not ru_insights and not cn_insights:
        parts.append("No significant new trends detected beyond baseline.")

    return " ".join(parts)


def build_pdf_report_text(
    ru_insights: List[Dict],
    cn_insights: List[Dict],
    crisis_alerts: List[Dict],
    executive_summary: str,
) -> str:
    """Generate the 1-page 'Diplomatic Dividend' special report text."""
    lines: List[str] = []
    lines.append("=" * 62)
    lines.append("  THE DIPLOMATIC DIVIDEND -- SPECIAL REPORT")
    lines.append("  What Russia & China Are Saying About Tanzania This Week")
    lines.append("=" * 62)
    lines.append(
        f"  Generated: "
        f"{datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}"
    )
    lines.append("")

    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 62)
    lines.append(f"  {executive_summary}")
    lines.append("")

    if crisis_alerts:
        lines.append("CRISIS ALERTS")
        lines.append("-" * 62)
        for a in crisis_alerts[:3]:
            lines.append(
                f"  * [{a.get('platform','?')}] "
                f"{a.get('content_snippet','')[:120]}"
            )
        lines.append("")

    lines.append("KEY INSIGHTS")
    lines.append("-" * 62)
    for market, insights in [("RUSSIA", ru_insights), ("CHINA", cn_insights)]:
        if insights:
            lines.append(f"  {market}")
            for i in insights:
                lines.append(f"    Trend: {i['trend']}")
                lines.append(f"    Sentiment: {i['sentiment']}")
                lines.append(f"    Action: {i['action'][:100]}...")
    lines.append("")

    lines.append("STRATEGIC RECOMMENDATIONS")
    lines.append("-" * 62)
    for market, insights in [("Russia", ru_insights), ("China", cn_insights)]:
        for i in insights[:2]:
            lines.append(f"  * {market}: {i['action'][:150]}")
    lines.append("")
    lines.append("-" * 62)
    lines.append("Powered by Agent Reach -- Geopolitical Tourism Radar")
    lines.append("-" * 62)
    return "\n".join(lines)


# ------------------------------------------------------------------
# Main entry-point called from main.py background task
# ------------------------------------------------------------------


async def run_full_scan_and_translate(
    client_id: str, custom_keywords: List[str]
) -> Dict[str, Any]:
    """Runs concurrent Exa scans for China & Russia, then translates."""
    logger.info(
        f"Initiating run_full_scan_and_translate for client: {client_id}"
    )

    cn_posts, ru_posts = await asyncio.gather(
        scan_china_market(custom_keywords),
        scan_russia_market(custom_keywords),
    )

    total_posts = len(cn_posts) + len(ru_posts)
    logger.info(
        f"Scrape completed: gathered {total_posts} raw posts "
        f"({len(cn_posts)} CN, {len(ru_posts)} RU)"
    )

    import os

    report_date = datetime.now(timezone.utc).isoformat()

    if total_posts == 0:
        return {
            "status": "COMPLETED",
            "executiveSummary": (
                "No posts collected from Chinese or Russian markets. "
                "Try adjusting search keywords."
            ),
            "chinaInsights": [],
            "russiaInsights": [],
            "crisisAlerts": [],
            "reportDate": report_date,
            "raw_post_count": 0,
        }

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning(
            "OPENAI_API_KEY not found in environment. "
            "Falling back to heuristic analysis."
        )
        ru_insights, ru_crisis = analyze_russia_posts(ru_posts)
        cn_insights, cn_crisis = analyze_china_posts(cn_posts)
        crisis_alerts = ru_crisis + cn_crisis
        summary = build_executive_summary(
            ru_posts, cn_posts, ru_insights, cn_insights, crisis_alerts
        )
        return {
            "status": "COMPLETED",
            "executiveSummary": summary,
            "chinaInsights": cn_insights,
            "russiaInsights": ru_insights,
            "crisisAlerts": crisis_alerts,
            "reportDate": report_date,
            "raw_post_count": total_posts,
        }

    try:
        from openai import AsyncOpenAI

        openai_client = AsyncOpenAI(api_key=api_key)

        payload = {
            "china_posts": [
                {
                    "platform": p.get("platform"),
                    "author": p.get("author"),
                    "content_snippet": p.get("content_snippet"),
                    "url": p.get("url"),
                    "published": p.get("published"),
                    "is_crisis": p.get("is_crisis"),
                }
                for p in cn_posts
            ],
            "russia_posts": [
                {
                    "platform": p.get("platform"),
                    "author": p.get("author"),
                    "content_snippet": p.get("content_snippet"),
                    "url": p.get("url"),
                    "published": p.get("published"),
                    "is_crisis": p.get("is_crisis"),
                }
                for p in ru_posts
            ],
        }

        system_instruction = (
            "You are a professional geopolitical intelligence AI analyzing "
            "tourism market signals for Tanzania. Your task is to take raw "
            "social media and news posts from the Chinese market and Russian "
            "market, translate any Chinese or Russian text to English, and "
            "synthesize them into a structured report.\n\n"
            "You must respond with a JSON object containing:\n"
            "- 'executiveSummary' (string): 2-3 sentence overview\n"
            "- 'chinaInsights' (array): each with 'trend', 'sentiment', "
            "'action', 'posts'\n"
            "- 'russiaInsights' (array): same structure\n"
            "- 'crisisAlerts' (array): posts with severe issues\n\n"
            "Constraints:\n"
            "1. Valid JSON only, no markdown wrappers.\n"
            "2. Translate all content to natural English.\n"
            "3. Trends and actions must be specific to Tanzania tourism."
        )

        user_content = (
            f"Here is the raw data collected:\n"
            f"{json.dumps(payload, ensure_ascii=False)}"
        )

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        result_text = response.choices[0].message.content
        logger.info(
            f"OpenAI analysis completed. "
            f"Raw output: {result_text[:500]}..."
        )

        parsed_result = json.loads(result_text)

        return {
            "status": "COMPLETED",
            "executiveSummary": parsed_result.get(
                "executiveSummary", "Scan complete."
            ),
            "chinaInsights": parsed_result.get("chinaInsights", []),
            "russiaInsights": parsed_result.get("russiaInsights", []),
            "crisisAlerts": parsed_result.get("crisisAlerts", []),
            "reportDate": report_date,
            "raw_post_count": total_posts,
        }

    except Exception as e:
        logger.error(
            f"Error during OpenAI translation and analysis: {e}"
        )
        ru_insights, ru_crisis = analyze_russia_posts(ru_posts)
        cn_insights, cn_crisis = analyze_china_posts(cn_posts)
        crisis_alerts = ru_crisis + cn_crisis
        summary = build_executive_summary(
            ru_posts, cn_posts, ru_insights, cn_insights, crisis_alerts
        )
        return {
            "status": "COMPLETED",
            "executiveSummary": (
                f"{summary} (Note: AI translation failed, displaying "
                f"heuristic analysis. Error: {str(e)})"
            ),
            "chinaInsights": cn_insights,
            "russiaInsights": ru_insights,
            "crisisAlerts": crisis_alerts,
            "reportDate": report_date,
            "raw_post_count": total_posts,
        }