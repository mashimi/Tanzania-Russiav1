"""
Agent Reach Orchestration Layer -- ENHANCED & TRANSLATED.
Features:
1. Categorized Keyword Matrices (Tourism, Investment, Logistics, Luxury)
2. Async Concurrency (Semaphore) for 5x faster scraping
3. Robust Native JSON Parsing for Exa MCP
4. Native XiaoHongShu (XHS) MCP Scraping for authentic social signals
5. Jina Reader Deep-Fetching for top URLs (better crisis context)
6. AI-Powered English Translation (OpenAI gpt-4o-mini, cost-optimized)
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

# -- OpenAI Client Setup --
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. Translation will fallback to original text.")

# -- Keyword Matrices & Forum Targets --
FORUM_DOMAINS_RU = ["awd.ru", "tonkosti.ru", "forum.awd.ru", "pikabu.ru", "vk.com"]
FORUM_DOMAINS_CN = ["xiaohongshu.com", "zhihu.com", "weibo.com", "bilibili.com"]

KEYWORD_MATRIX_RU = {
    "tourism": [
        "\u0417\u0430\u043d\u0437\u0438\u0431\u0430\u0440 \u043e\u0442\u0434\u044b\u0445 2025",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0441\u0430\u0444\u0430\u0440\u0438 \u043e\u0442\u0437\u044b\u0432\u044b",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0442\u0443\u0440\u0438\u0437\u043c \u0432\u0441\u0435 \u0432\u043a\u043b\u044e\u0447\u0435\u043d\u043e",
        "\u0440\u043e\u0441\u0441\u0438\u0439\u0441\u043a\u0438\u0435 \u0442\u0443\u0440\u0438\u0441\u0442\u044b \u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0432\u0438\u0437\u0430 \u043d\u043e\u0432\u043e\u0441\u0442\u0438",
    ],
    "investment": [
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0438\u043d\u0432\u0435\u0441\u0442\u0438\u0446\u0438\u0438 2025",
        "\u0417\u0430\u043d\u0437\u0438\u0431\u0430\u0440 \u0431\u0438\u0437\u043d\u0435\u0441 \u0434\u0435\u043b\u0435\u0433\u0430\u0446\u0438\u044f",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0420\u043e\u0441\u0441\u0438\u044f \u044d\u043a\u043e\u043d\u043e\u043c\u0438\u043a\u0430",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0421\u0430\u043c\u0438\u044f \u0421\u0443\u043b\u0443\u0445\u0443 \u0425\u0430\u0441\u0441\u0430\u043d",
        "\u0417\u0430\u043d\u0437\u0438\u0431\u0430\u0440 \u0438\u043d\u0432\u0435\u0441\u0442\u0438\u0446\u0438\u0438",
        "\u0422\u0430\u043d\u0437\u0430\u043d\u0438\u044f \u0420\u043e\u0441\u0441\u0438\u044f \u0442\u0443\u0440\u0438\u0437\u043c \u043f\u0430\u0440\u0442\u043d\u0451\u0440\u0441\u0442\u0432\u043e",
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
    ],
}

KEYWORD_MATRIX_CN = {
    "tourism": [
        "\u5766\u6851\u5c3c\u4e9a \u65c5\u6e38\u653b\u7565",
        "\u6851\u7ed9\u5df4\u5c14 \u9152\u5e97 \u63a8\u8350",
        "\u5766\u6851\u5c3c\u4e9a \u6e38\u730e \u907f\u5751",
        "\u5766\u6851\u5c3c\u4e9a \u585e\u4f26\u76d6\u8482 \u52a8\u7269\u5927\u8fc1\u5f99",
        "\u5766\u6851\u5c3c\u4e9a \u4e03\u529b\u9a6c\u624e\u7f57 \u767b\u5c71",
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
    ],
}


def get_all_keywords(
    matrix: dict, custom_keywords: Optional[List[str]] = None
) -> List[str]:
    flat_list = [kw for category in matrix.values() for kw in category]
    if custom_keywords:
        flat_list.extend(custom_keywords)
    return list(dict.fromkeys(flat_list))


# -- Crisis & Pattern Detection --
CRISIS_PATTERNS_RU = [
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
CRISIS_PATTERNS_CN = [
    "\u907f\u5751", "\u7593\u75be", "\u5bb0\u5ba2",
    "\u8bc8\u9a97", "\u5371\u9669", "\u62a2\u52ab",
    "\u751f\u75c5", "\u4e8b\u6545",
]

PAYMENT_PATTERNS_RU = [
    r"\u043e\u043f\u043b\u0430\u0442\u0430",
    r"\u043a\u0430\u0440\u0442\u0430",
    r"\u0434\u0435\u043d\u044c\u0433\u0438",
    r"\u043f\u0435\u0440\u0435\u0432\u043e\u0434",
]
VISA_PATTERNS_RU = [
    r"\u0432\u0438\u0437\u0430",
    r"\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442",
    r"\u043f\u0430\u0441\u043f\u043e\u0440\u0442",
    r"\u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d",
]
FLIGHT_PATTERNS_RU = [
    r"\u0440\u0435\u0439\u0441",
    r"\u0431\u0438\u043b\u0435\u0442",
    r"\u0430\u0432\u0438\u0430",
    r"\u0447\u0430\u0440\u0442\u0435\u0440",
]
FLIGHT_PATTERNS_CN = [
    "\u822a\u73ed", "\u76f4\u98de", "\u673a\u7968", "\u5305\u673a",
]

# -- Concurrency Control --
EXA_SEMAPHORE = asyncio.Semaphore(3)
XHS_SEMAPHORE = asyncio.Semaphore(2)


# -- Helper: Mcporter Path --
def _get_mcporter_path() -> Optional[str]:
    import os as _os
    npm_global = _os.path.expanduser("~\\AppData\\Roaming\\npm")
    win_mcporter = _os.path.join(npm_global, "mcporter.cmd")
    if _os.path.isfile(win_mcporter):
        return win_mcporter
    return shutil.which("mcporter") or shutil.which("mcporter.cmd")


def _check_mcporter() -> bool:
    mcporter = _get_mcporter_path()
    if not mcporter:
        return False
    try:
        r = subprocess.run(
            [mcporter, "config", "list"],
            capture_output=True, encoding="utf-8", timeout=5,
        )
        return "exa" in r.stdout.lower()
    except Exception:
        return False


# -- Helper: Jina Deep Fetch --
async def fetch_jina_content(url: str) -> str:
    if not url or not url.startswith("http"):
        return ""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["curl", "-s", "-m", "10", jina_url],
                capture_output=True, timeout=15,
            ),
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace")[:1500]
    except Exception:
        pass
    return ""


# -- Helper: AI Translation --
async def translate_to_english(text: str) -> str:
    if not text or not openai_client or len(text) < 10:
        return text
    if re.match(r"^[A-Za-z0-9\s\-\_\.\,\!\?]+$", text):
        return text
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate the following text to professional, "
                        "business-appropriate English. Preserve proper nouns."
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
    translated_insights = []
    for insight in insights:
        translated_insights.append({
            "trend": await translate_to_english(insight["trend"]),
            "sentiment": insight["sentiment"],
            "action": await translate_to_english(insight["action"]),
            "posts": [
                {
                    "platform": p["platform"],
                    "author": p["author"],
                    "content_snippet": await translate_to_english(
                        p["content_snippet"][:150]
                    ),
                    "engagement": p.get("engagement", 0),
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in insight.get("posts", [])[:2]
            ]
            if insight.get("posts")
            else [],
        })

    translated_alerts = []
    for alert in crisis_alerts[:3]:
        translated_alerts.append({
            "platform": alert.get("platform", "Unknown"),
            "author": alert.get("author", "Unknown"),
            "content_snippet": await translate_to_english(
                alert.get("content_snippet", "")[:150]
            ),
            "engagement": alert.get("engagement", 0),
            "is_crisis": True,
        })

    return translated_insights, translated_alerts


# -- Core Scanners --
async def run_exa_search_safe(
    keyword: str,
    num_results: int = 5,
    include_domains: Optional[List[str]] = None,
) -> str:
    mcporter = _get_mcporter_path()
    if not mcporter:
        return ""

    domains_str = (
        f", includeDomains: {json.dumps(include_domains)}"
        if include_domains
        else ""
    )
    cmd = [
        mcporter, "call",
        f'exa.web_search_exa(query: "{keyword}", numResults: {num_results}{domains_str})',
    ]

    async with EXA_SEMAPHORE:
        logger.info(f"Exa searching: {keyword}")
        loop = asyncio.get_event_loop()
        try:
            def _run():
                return subprocess.run(cmd, capture_output=True, timeout=30)

            result = await loop.run_in_executor(None, _run)
            if result.returncode != 0:
                stderr_text = result.stderr.decode("utf-8", errors="replace")[:100]
                logger.warning(f"Exa failed for '{keyword}': {stderr_text}")
                return ""
            return result.stdout.decode("utf-8", errors="replace").strip()
        except Exception as e:
            logger.error(f"Exa exception for '{keyword}': {e}")
            return ""


def _parse_exa_json_output(output: str) -> List[Dict[str, Any]]:
    if not output:
        return []
    try:
        data = json.loads(output)
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", "No Title"),
                "url": item.get("url", ""),
                "published": item.get("publishedDate", ""),
                "author": item.get("author", "Unknown"),
                "text": item.get("text", "")[:600],
                "score": item.get("score", 0),
            })
        return results
    except (json.JSONDecodeError, TypeError):
        pass

    logger.info("Exa output not JSON; parsing as text block.")
    results = []
    blocks = re.split(r"\n---\n", output.strip())
    for block in blocks:
        if not block.strip():
            continue
        title = url = published = author = highlights = ""
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
                cleaned = re.sub(r"\[\.\.\.\]", "", line).strip()
                if cleaned:
                    highlight_lines.append(cleaned)
        highlights = " ".join(highlight_lines)
        text_val = highlights[:600] if highlights else title
        if title or highlights:
            results.append({
                "title": title,
                "url": url,
                "published": published,
                "author": author if author and author != "N/A" else "Unknown",
                "text": text_val,
                "score": 0,
            })
    return results


async def scan_xiaohongshu_market(
    custom_keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    mcporter = _get_mcporter_path()
    if not mcporter:
        return []

    xhs_keywords = [
        "Tanzania lv you",
        "Sanggeiba er gong lue",
        "Tanzania bi keng",
        "Fei zhou you lie",
    ] + (custom_keywords or [])
    xhs_keywords = list(dict.fromkeys(xhs_keywords))
    all_posts = []

    async def fetch_xhs(kw: str) -> None:
        async with XHS_SEMAPHORE:
            cmd = [mcporter, "call", f'xiaohongshu.search_feeds(keyword: "{kw}")']
            try:
                loop = asyncio.get_event_loop()
                def _run():
                    return subprocess.run(
                        cmd, capture_output=True, timeout=20,
                        shell=mcporter.lower().endswith(".cmd"),
                    )
                result = await loop.run_in_executor(None, _run)
                if result.returncode == 0:
                    data = json.loads(
                        result.stdout.decode("utf-8", errors="replace")
                    )
                    for item in data.get("items", [])[:3]:
                        note = item.get("note_card", {})
                        content = f"{note.get('title', '')}: {note.get('desc', '')}"
                        all_posts.append({
                            "platform": "XiaoHongShu",
                            "author": note.get("user", {}).get("nickname", "Unknown"),
                            "content_snippet": content[:250],
                            "engagement": int(
                                note.get("interact_info", {}).get("liked_count", 0)
                            ),
                            "is_crisis": any(k in content for k in CRISIS_PATTERNS_CN),
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

    all_posts = []
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

    all_posts = []
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

    xhs_posts = await scan_xiaohongshu_market(custom_keywords)
    all_posts.extend(xhs_posts)
    return all_posts


# -- Heuristic Analysis (Original Language) --

def analyze_russia_posts(
    posts: List[Dict[str, Any]],
) -> Tuple[List[Dict], List[Dict]]:
    insights = []
    crisis_alerts = [p for p in posts if p.get("is_crisis")]
    if not posts:
        return insights, crisis_alerts

    payment_posts = [
        p for p in posts
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
        p for p in posts
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
        p for p in posts
        if _detect_crisis(p.get("content_snippet", ""), FLIGHT_PATTERNS_RU)
    ]
    if flight_posts:
        insights.append({
            "trend": "Flights & Logistics / Aviabilety",
            "sentiment": "Positive",
            "action": "Promote new Air Tanzania direct flights from Moscow. Create Moscow to Zanzibar packages.",
            "posts": flight_posts[:2],
        })

    return insights, crisis_alerts


def analyze_china_posts(
    posts: List[Dict[str, Any]],
) -> Tuple[List[Dict], List[Dict]]:
    insights = []
    crisis_alerts = [p for p in posts if p.get("is_crisis")]
    if not posts:
        return insights, crisis_alerts

    flight_cn = [
        p for p in posts
        if _detect_crisis(p.get("content_snippet", ""), FLIGHT_PATTERNS_CN)
    ]
    if flight_cn:
        insights.append({
            "trend": "Direct Flight Discussion",
            "sentiment": "Positive",
            "action": "Publish Chinese content about new flight connections.",
            "posts": flight_cn[:2],
        })

    invest_cn = [
        p for p in posts
        if any(
            kw in p.get("content_snippet", "")
            for kw in ["\u6295\u8d44", "\u5408\u4f5c", "\u7ecf\u8d38", "\u4e00\u5e26\u4e00\u8def"]
        )
    ]
    if invest_cn:
        insights.append({
            "trend": "Belt & Road Investment",
            "sentiment": "Positive",
            "action": "Publish Mandarin case studies on WeChat Official Accounts.",
            "posts": invest_cn[:2],
        })

    visa_cn = [
        p for p in posts
        if any(
            kw in p.get("content_snippet", "")
            for kw in ["\u7b7e\u8bc1", "\u653f\u7b56", "\u5165\u5883"]
        )
    ]
    if visa_cn:
        insights.append({
            "trend": "Visa Policy Queries",
            "sentiment": "Neutral",
            "action": "Ensure visa-on-arrival info is displayed on XiaoHongShu and Weibo.",
            "posts": visa_cn[:2],
        })

    return insights, crisis_alerts


# -- Main Orchestrator --

async def run_full_scan_and_translate(
    client_id: str, custom_keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    logger.info("Starting enhanced multi-market scan with deep-fetch and translation...")

    cn_posts, ru_posts = await asyncio.gather(
        scan_china_market_enhanced(custom_keywords),
        scan_russia_market_enhanced(custom_keywords),
    )

    ru_insights, ru_crisis = analyze_russia_posts(ru_posts)
    cn_insights, cn_crisis = analyze_china_posts(cn_posts)

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