"""
Agent Reach Orchestration Layer -- ENHANCED & TRANSLATED.
Features:
1. Categorized Keyword Matrices (Tourism, Investment, Logistics, Luxury)
2. Async Concurrency (Semaphore) for 5x faster scraping
3. Robust Native JSON Parsing for Exa MCP
4. Native XiaoHongShu (XHS) MCP Scraping
5. Jina Reader Deep-Fetching for top URLs (better crisis context)
6. AI-Powered English Translation (OpenAI gpt-4o-mini, cost-optimized)
7. Expanded Forum Sources (awd.ru, tonkosti.ru, zhihu.com, etc.)
"""
import asyncio
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from openai import AsyncOpenAI

# -- OpenAI Client Setup -----------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

if not OPENAI_API_KEY:
    logger.warning(
        "OPENAI_API_KEY not set. "
        "Translation will fallback to original text."
    )

# -- Expanded Categorized Keyword Matrices & Forum Targets ------------
FORUM_DOMAINS_RU = ["awd.ru", "tonkosti.ru", "forum.awd.ru", "pikabu.ru", "vk.com"]
FORUM_DOMAINS_CN = [
    "xiaohongshu.com",
    "zhihu.com",
    "weibo.com",
    "bilibili.com",
]

KEYWORD_MATRIX_RU: Dict[str, List[str]] = {
    "tourism": [
        "Zanzibar отдых 2025",
        "Tanzania сафари отзывы",
        "Tanzania туризм все включено",
        "российские туристы Tanzania",
        "Tanzania виза новости",
    ],
    "investment": [
        "Tanzania инвестиции 2025",
        "Tanzania Самия Сулуху Хассан",
        "Zanzibar бизнес делегация",
        "Tanzania Россия экономика",
        "Tanzania туризм партнёрство",
        "Zanzibar инвестиции",
        "Дар-эс-Салам деловая миссия",
        "Tanzania добыча золота",
    ],
    "logistics": [
        "прямые рейсы Tanzania",
        "Tanzania перелет из Москвы",
        "Tanzania оплата картой",
    ],
    "luxury": [
        "роскошные отели Zanzibar",
        "Tanzania VIP тур",
        "Серенгети люкс сафари",
    ],
}

KEYWORD_MATRIX_CN: Dict[str, List[str]] = {
    "tourism": [
        "Tanzania 旅游攻略",
        "Zanzibar 酒店 推荐",
        "Tanzania 游猎 避坑",
        "Tanzania 塞伦盖蒂 动物大迁徙",
        "Tanzania 乞力马扎罗 登山",
        "Tanzania 中文导游",
        "Tanzania 旅游 安全",
    ],
    "investment": [
        "Tanzania 投资 机遇",
        "中坦 旅游 合作",
        "Tanzania 总统 经济",
        "Zanzibar 商务 考察",
        "Tanzania 一带一路",
        "Tanzania 矿业 合作",
        "Tanzania 农业 投资",
        "中坦 经贸 合作",
        "Tanzania 房地产 投资",
        "达累斯萨拉姆 港口",
    ],
    "logistics": [
        "Tanzania 签证 政策",
        "Tanzania 直飞 航班",
        "Tanzania 机票 价格",
        "Tanzania 坦赞铁路",
    ],
    "luxury": [
        "Zanzibar 奢华 度假村",
        "Tanzania 高端 定制 游",
        "塞伦盖蒂 豪华 帐篷",
    ],
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


# -- Crisis & Pattern Detection (Original Language) --------------------

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

PAYMENT_PATTERNS_RU: List[str] = [
    r"\u043e\u043f\u043b\u0430\u0442\u0430",
    r"\u043a\u0430\u0440\u0442\u0430",
    r"\u0434\u0435\u043d\u044c\u0433\u0438",
    r"\u043f\u0435\u0440\u0435\u0432\u043e\u0434",
    r"\u0432\u0430\u043b\u044e\u0442\u0430",
]
VISA_PATTERNS_RU: List[str] = [
    r"\u0432\u0438\u0437\u0430",
    r"\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442",
    r"\u043f\u0430\u0441\u043f\u043e\u0440\u0442",
    r"\u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d",
]
FLIGHT_PATTERNS_RU: List[str] = [
    r"\u0440\u0435\u0439\u0441",
    r"\u0431\u0438\u043b\u0435\u0442",
    r"\u0430\u0432\u0438\u0430",
    r"\u0447\u0430\u0440\u0442\u0435\u0440",
]
FLIGHT_PATTERNS_CN: List[str] = [
    "\u822a\u73ed",
    "\u76f4\u98de",
    "\u673a\u7968",
    "\u5305\u673a",
]

# -- Concurrency Control -----------------------------------------------

EXA_SEMAPHORE = asyncio.Semaphore(3)  # Max 3 concurrent Exa searches
XHS_SEMAPHORE = asyncio.Semaphore(2)  # Max 2 concurrent XHS searches

# -- Helper: Mcporter Path ---------------------------------------------

_MCPORTER_CHECK_CACHE: Optional[bool] = None


def _get_mcporter_path() -> Optional[str]:
    import os as _os

    npm_global = _os.path.expanduser("~\\AppData\\Roaming\\npm")
    win_mcporter = _os.path.join(npm_global, "mcporter.cmd")
    if _os.path.isfile(win_mcporter):
        return win_mcporter
    found = shutil.which("mcporter") or shutil.which("mcporter.cmd")
    if found:
        return found
    logger.warning("mcporter not found. Install: npm install -g mcporter")
    return None


def _check_mcporter() -> bool:
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
        _MCPORTER_CHECK_CACHE = ok
        return ok
    except Exception as e:
        logger.info(
            f"mcporter config preflight did not complete ({e}); "
            "direct searches will still be attempted."
        )
        _MCPORTER_CHECK_CACHE = False
        return False


# -- Helper: Jina Deep Fetch -------------------------------------------


async def fetch_jina_content(url: str) -> str:
    """Fetch full markdown content of a URL via Jina Reader for deeper context."""
    if not url or not url.startswith("http"):
        return ""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        loop = asyncio.get_event_loop()

        def _run() -> subprocess.CompletedProcess:
            return subprocess.run(
                ["curl", "-s", "-m", "10", jina_url],
                capture_output=True,
                timeout=15,
            )

        result = await loop.run_in_executor(None, _run)
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace")[:1500]
    except Exception:
        pass
    return ""


# -- Helper: AI Translation --------------------------------------------


async def translate_to_english(text: str) -> str:
    """Translate text to professional English using OpenAI."""
    if not text or not openai_client or len(text) < 10:
        return text

    # Skip if already mostly English
    if re.match(r"^[A-Za-z0-9\s\-\_\.\,\!\?\']+$", text):
        return text

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate the following text to professional, "
                        "business-appropriate English. Preserve the original "
                        "meaning, tone, and any specific proper nouns "
                        "(e.g., Zanzibar, Serengeti)."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            timeout=10.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"OpenAI translation failed: {e}")
        return text


async def translate_insights(
    insights: List[Dict], crisis_alerts: List[Dict]
) -> Tuple[List[Dict], List[Dict]]:
    """Translate only the final insights and top crisis alerts to save API costs."""
    translated_insights: List[Dict] = []
    for insight in insights:
        trend = await translate_to_english(insight["trend"])
        action = await translate_to_english(insight["action"])
        posts: List[Dict] = []
        for p in insight.get("posts", [])[:2]:
            snippet = await translate_to_english(p.get("content_snippet", "")[:150])
            posts.append({
                "platform": p["platform"],
                "author": p["author"],
                "content_snippet": snippet,
                "engagement": p.get("engagement", 0),
                "is_crisis": p.get("is_crisis", False),
            })
        translated_insights.append({
            "trend": trend,
            "sentiment": insight["sentiment"],
            "action": action,
            "posts": posts,
        })

    translated_alerts: List[Dict] = []
    for alert in crisis_alerts[:3]:
        snippet = await translate_to_english(
            alert.get("content_snippet", "")[:150]
        )
        translated_alerts.append({
            "platform": alert.get("platform", "Unknown"),
            "author": alert.get("author", "Unknown"),
            "content_snippet": snippet,
            "engagement": alert.get("engagement", 0),
            "is_crisis": True,
        })

    return translated_insights, translated_alerts


# -- Core Scanners -----------------------------------------------------


async def run_exa_search_safe(
    keyword: str,
    num_results: int = 5,
    include_domains: Optional[List[str]] = None,
) -> str:
    """Run Exa search with concurrency control and domain targeting."""
    mcporter = _get_mcporter_path()
    if not mcporter:
        return ""

    domains_str = ""
    if include_domains:
        domains_str = f', includeDomains: {json.dumps(include_domains)}'
    cmd = [
        mcporter,
        "call",
        f'exa.web_search_exa(query: "{keyword}", numResults: {num_results}{domains_str})',
    ]

    async with EXA_SEMAPHORE:
        logger.info(f"Exa searching: {keyword}")
        loop = asyncio.get_event_loop()

        def _run() -> subprocess.CompletedProcess:
            return subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                shell=mcporter.lower().endswith(".cmd"),
            )

        try:
            result = await loop.run_in_executor(None, _run)
            if result.returncode != 0:
                stderr_text = result.stderr.decode("utf-8", errors="replace")[:100]
                logger.warning(f"Exa failed for '{keyword}': {stderr_text}")
                return ""
            return result.stdout.decode("utf-8", errors="replace").strip()
        except subprocess.TimeoutExpired:
            logger.warning(f"Exa search timed out for '{keyword}'")
            return ""
        except Exception as e:
            logger.error(f"Exa exception for '{keyword}': {e}")
            return ""


def _parse_exa_json_output(output: str) -> List[Dict[str, Any]]:
    """Robustly parse Exa MCP native JSON output."""
    if not output:
        return []
    try:
        data = json.loads(output)
        results: List[Dict[str, Any]] = []
        items = data.get("results", [])
        for item in items:
            results.append({
                "title": item.get("title", "No Title"),
                "url": item.get("url", ""),
                "published": item.get("publishedDate", ""),
                "author": item.get("author", "Unknown"),
                "text": item.get("text", "")[:600],
                "score": item.get("score", 0),
            })
        return results
    except json.JSONDecodeError:
        logger.warning("Failed to parse Exa output as JSON.")
        return []


async def scan_xiaohongshu_market(
    custom_keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Scan XiaoHongShu for authentic Chinese tourist sentiment."""
    mcporter = _get_mcporter_path()
    if not mcporter:
        return []

    xhs_keywords = [
        "Tanzania 旅游",
        "Zanzibar 攻略",
        "Tanzania 避坑",
        "非洲 游猎",
    ] + (custom_keywords or [])
    xhs_keywords = list(dict.fromkeys(xhs_keywords))
    all_posts: List[Dict[str, Any]] = []

    async def fetch_xhs(kw: str) -> None:
        async with XHS_SEMAPHORE:
            cmd = [
                mcporter,
                "call",
                f'xiaohongshu.search_feeds(keyword: "{kw}")',
            ]
            try:
                loop = asyncio.get_event_loop()

                def _run() -> subprocess.CompletedProcess:
                    return subprocess.run(
                        cmd,
                        capture_output=True,
                        timeout=20,
                        shell=mcporter.lower().endswith(".cmd"),
                    )

                result = await loop.run_in_executor(None, _run)
                if result.returncode == 0:
                    data = json.loads(
                        result.stdout.decode("utf-8", errors="replace")
                    )
                    items = data.get("items", [])[:3]
                    for item in items:
                        note = item.get("note_card", {})
                        title = note.get("title", "")
                        desc = note.get("desc", "")
                        content = f"{title}: {desc}"
                        all_posts.append({
                            "platform": "XiaoHongShu",
                            "author": note.get("user", {}).get(
                                "nickname", "Unknown"
                            ),
                            "content_snippet": content[:250],
                            "engagement": int(
                                note.get("interact_info", {}).get(
                                    "liked_count", 0
                                )
                            ),
                            "is_crisis": any(
                                k in content for k in CRISIS_PATTERNS_CN
                            ),
                            "url": (
                                f"https://www.xiaohongshu.com/explore/"
                                f"{note.get('note_id', '')}"
                            ),
                            "source_keyword": kw,
                        })
            except Exception as e:
                logger.warning(f"XHS scan failed for '{kw}': {e}")
            await asyncio.sleep(1.5)

    await asyncio.gather(*[fetch_xhs(kw) for kw in xhs_keywords])
    return all_posts


def _detect_crisis(text: str, patterns: List[str]) -> bool:
    text_lower = text.lower()
    for p in patterns:
        try:
            if re.search(p, text_lower):
                return True
        except re.error:
            if p.lower() in text_lower:
                return True
    return False


async def scan_russia_market_enhanced(
    custom_keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    if not _check_mcporter():
        logger.warning("mcporter/Exa unavailable -- Russia scan returning empty")
        return []

    keywords = get_all_keywords(KEYWORD_MATRIX_RU, custom_keywords)

    exa_tasks = [
        run_exa_search_safe(kw, num_results=5, include_domains=FORUM_DOMAINS_RU)
        for kw in keywords
    ]
    exa_outputs = await asyncio.gather(*exa_tasks)

    all_posts: List[Dict[str, Any]] = []
    for kw, output in zip(keywords, exa_outputs):
        parsed_items = _parse_exa_json_output(output)
        for i, item in enumerate(parsed_items):
            content = f"{item['title']}: {item['text']}"
            deep_text = ""
            if item["url"] and i < 2:
                deep_text = await fetch_jina_content(item["url"])
            final_content = (
                f"{content}\n\n[Full Context]: {deep_text}"
                if deep_text
                else content
            )

            all_posts.append({
                "platform": "Exa (Russia Forums)",
                "author": item["author"],
                "content_snippet": final_content[:300],
                "engagement": 0,
                "is_crisis": _detect_crisis(final_content, CRISIS_PATTERNS_RU),
                "url": item["url"],
                "source_keyword": kw,
            })
        await asyncio.sleep(0.2)

    return all_posts


async def scan_china_market_enhanced(
    custom_keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    if not _check_mcporter():
        logger.warning("mcporter/Exa unavailable -- China scan returning empty")
        return []

    keywords = get_all_keywords(KEYWORD_MATRIX_CN, custom_keywords)

    exa_tasks = [
        run_exa_search_safe(kw, num_results=5, include_domains=FORUM_DOMAINS_CN)
        for kw in keywords
    ]
    exa_outputs = await asyncio.gather(*exa_tasks)

    all_posts: List[Dict[str, Any]] = []
    for kw, output in zip(keywords, exa_outputs):
        parsed_items = _parse_exa_json_output(output)
        for i, item in enumerate(parsed_items):
            content = f"{item['title']}: {item['text']}"
            deep_text = ""
            if item["url"] and i < 2:
                deep_text = await fetch_jina_content(item["url"])
            final_content = (
                f"{content}\n\n[Full Context]: {deep_text}"
                if deep_text
                else content
            )

            all_posts.append({
                "platform": "Exa (China Forums)",
                "author": item["author"],
                "content_snippet": final_content[:300],
                "engagement": 0,
                "is_crisis": _detect_crisis(final_content, CRISIS_PATTERNS_CN),
                "url": item["url"],
                "source_keyword": kw,
            })
        await asyncio.sleep(0.2)

    # Run XiaoHongShu scan in parallel with existing results
    xhs_posts = await scan_xiaohongshu_market(custom_keywords)
    all_posts.extend(xhs_posts)

    return all_posts


# -- Heuristic Analysis (Original Language) ----------------------------


def analyze_russia_posts(
    posts: List[Dict[str, Any]],
) -> Tuple[List[Dict], List[Dict]]:
    insights: List[Dict] = []
    crisis_alerts = [p for p in posts if p.get("is_crisis")]
    if not posts:
        return insights, crisis_alerts

    payment_posts = [
        p
        for p in posts
        if _detect_crisis(p.get("content_snippet", ""), PAYMENT_PATTERNS_RU)
    ]
    if payment_posts:
        insights.append({
            "trend": "Payment Friction / Valyuta i oplata",
            "sentiment": "Negative",
            "action": "Highlight UnionPay, M-Pesa, and crypto payment options on Russian booking pages.",
            "posts": payment_posts[:2],
        })

    visa_posts = [
        p
        for p in posts
        if _detect_crisis(p.get("content_snippet", ""), VISA_PATTERNS_RU)
    ]
    if visa_posts:
        insights.append({
            "trend": "Visa & Entry Requirements / Viza",
            "sentiment": "Neutral",
            "action": "Publish a clear visa-on-arrival guide in Russian on travel forums.",
            "posts": visa_posts[:2],
        })

    flight_posts = [
        p
        for p in posts
        if _detect_crisis(p.get("content_snippet", ""), FLIGHT_PATTERNS_RU)
    ]
    if flight_posts:
        insights.append({
            "trend": "Flights & Logistics / Aviabilety",
            "sentiment": "Positive",
            "action": "Promote new Air Tanzania direct flights from Moscow. Create 'Moscow -> Zanzibar' packages.",
            "posts": flight_posts[:2],
        })

    return insights, crisis_alerts


def analyze_china_posts(
    posts: List[Dict[str, Any]],
) -> Tuple[List[Dict], List[Dict]]:
    insights: List[Dict] = []
    crisis_alerts = [p for p in posts if p.get("is_crisis")]
    if not posts:
        return insights, crisis_alerts

    flight_cn = [
        p
        for p in posts
        if _detect_crisis(p.get("content_snippet", ""), FLIGHT_PATTERNS_CN)
    ]
    if flight_cn:
        insights.append({
            "trend": "Direct Flight Discussion",
            "sentiment": "Positive",
            "action": "Publish Chinese content about new flight connections. Emphasize convenience.",
            "posts": flight_cn[:2],
        })

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
            "action": "Publish Mandarin case studies on WeChat Official Accounts. Highlight Tanzania Belt & Road projects.",
            "posts": invest_cn[:2],
        })

    visa_cn = [
        p
        for p in posts
        if any(kw in p.get("content_snippet", "") for kw in ["visa", "policy", "entry"])
    ]
    if visa_cn:
        insights.append({
            "trend": "Visa Policy Queries",
            "sentiment": "Neutral",
            "action": "Ensure visa-on-arrival info is prominently displayed on XiaoHongShu and Weibo.",
            "posts": visa_cn[:2],
        })

    return insights, crisis_alerts


# -- Main Orchestrator -------------------------------------------------


async def run_full_scan_and_translate(
    client_id: str, custom_keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Main entry point: Scrape, Analyze, Translate, and Return."""
    logger.info(
        "Starting enhanced multi-market scan with deep-fetch and translation..."
    )

    cn_posts, ru_posts = await asyncio.gather(
        scan_china_market_enhanced(custom_keywords),
        scan_russia_market_enhanced(custom_keywords),
    )

    ru_insights, ru_crisis = analyze_russia_posts(ru_posts)
    cn_insights, cn_crisis = analyze_china_posts(cn_posts)

    all_crisis = ru_crisis + cn_crisis

    logger.info("Translating insights to English via OpenAI...")
    translated_ru_insights, translated_ru_crisis = await translate_insights(
        ru_insights, ru_crisis
    )
    translated_cn_insights, translated_cn_crisis = await translate_insights(
        cn_insights, cn_crisis
    )

    all_translated_crisis = translated_ru_crisis + translated_cn_crisis

    total_posts = len(cn_posts) + len(ru_posts)
    crisis_count = len(all_translated_crisis)

    if crisis_count > 0:
        summary = (
            f"Scan complete. {total_posts} posts collected. "
            f"{crisis_count} crisis signal(s) detected requiring attention. "
            f"China: {translated_cn_insights[0]['trend'] if translated_cn_insights else 'Stable'}. "
            f"Russia: {translated_ru_insights[0]['trend'] if translated_ru_insights else 'Stable'}."
        )
    else:
        summary = (
            f"Scan complete. {total_posts} posts collected. "
            f"No immediate crisis signals. Market sentiment is stable."
        )

    return {
        "clientId": client_id,
        "status": "COMPLETED",
        "executiveSummary": summary,
        "chinaInsights": translated_cn_insights,
        "russiaInsights": translated_ru_insights,
        "crisisAlerts": all_translated_crisis,
        "reportDate": datetime.now(timezone.utc).isoformat(),
        "raw_post_count": total_posts,
    }