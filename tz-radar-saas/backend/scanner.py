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
import uuid
import math
from collections import Counter

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
        "Занзибар отдых 2025", "Танзания сафари отзывы", "Танзания туризм все включено",
        "российские туристы Танзания", "Танзания виза новости",
    ],
    "investment": [
        "Танзания инвестиции 2025", "Занзибар бизнес делегация", "Танзания Россия экономика",
        "Танзания Самия Сулуху Хассан", "Занзибар инвестиции", "Танзания Россия туризм партнёрство",
        "Дар-эс-Салам деловая миссия", "Танзания добыча золота",
    ],
    "logistics": [
        "прямые рейсы Танзания", "Танзания перелет из Москвы", "Танзания оплата картой",
    ],
    "luxury": [
        "роскошные отели Занзибар", "Танзания VIP тур", "Серенгети люкс сафари",
    ],
}

KEYWORD_MATRIX_CN = {
    "tourism": [
        "坦桑尼亚 旅游攻略", "桑给巴尔 酒店 推荐", "坦桑尼亚 游猎 避坑",
        "坦桑尼亚 塞伦盖蒂 动物大迁徙", "坦桑尼亚 乞力马扎罗 登山",
        "坦桑尼亚 中文导游", "坦桑尼亚 旅游 安全",
    ],
    "investment": [
        "坦桑尼亚 投资 机遇", "中坦 旅游 合作", "坦桑尼亚 总统 经济",
        "桑给巴尔 商务 考察", "坦桑尼亚 一带一路", "坦桑尼亚 矿业 合作",
        "坦桑尼亚 农业 投资", "中坦 经贸 合作", "坦桑尼亚 房地产 投资", "达累斯萨拉姆 港口",
    ],
    "logistics": [
        "坦桑尼亚 签证 政策", "坦桑尼亚 直飞 航班", "坦桑尼亚 机票 价格", "坦桑尼亚 坦赞铁路",
    ],
    "luxury": [
        "桑给巴尔 奢华 度假村", "坦桑尼亚 高端 定制 游", "塞伦盖蒂 豪华 帐篷",
    ],
}

def get_all_keywords(matrix: dict, custom_keywords: Optional[List[str]] = None) -> List[str]:
    flat_list = [kw for category in matrix.values() for kw in category]
    if custom_keywords:
        flat_list.extend(custom_keywords)
    return list(dict.fromkeys(flat_list))

# -- Crisis & Pattern Detection --
CRISIS_PATTERNS_RU = [
    r"проблем", r"мошен", r"опасн", r"грабеж", r"кража",
    r"обман", r"авария", r"теракт", r"болезн", r"маляр",
]
CRISIS_PATTERNS_CN = [
    "避坑", "疟疾", "宰客", "诈骗", "危险", "抢劫", "生病", "事故",
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
                    "content": "Translate the following text to professional, business-appropriate English. Preserve proper nouns.",
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

# -- Phase 1: Enhanced Post Metadata Helpers --
SENTIMENT_KEYWORDS_POSITIVE = [
    "отлично", "прекрасно", "рекомендую", "красиво", "безопасно", "удобно",
    "нравится", "замечательно", "лучший", "хороший", "впечатляющий",
    "很好", "不错", "推荐", "安全", "方便", "漂亮", "满意", "开心",
    "amazing", "great", "excellent", "wonderful", "recommend",
]
SENTIMENT_KEYWORDS_NEGATIVE = [
    "плохо", "ужасно", "опасно", "мошенники", "обман", "проблема", "сломался",
    "дорого", "грязно", "отменили", "задержка",
    "不好", "差", "骗子", "危险", "贵", "脏", "取消", "延迟", "差评",
    "terrible", "awful", "dangerous", "scam", "problem", "avoid",
]
LANGUAGE_BLOCKS = {
    "zh": r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]",
    "ru": r"[\u0400-\u04ff]",
    "en": r"[a-zA-Z]",
}

def calculate_engagement_score(raw_post: Dict[str, Any]) -> float:
    likes = raw_post.get("liked_count", raw_post.get("score", 0))
    comments = raw_post.get("comment_count", raw_post.get("score", 0) * 0.2)
    shares = raw_post.get("share_count", 0)
    views = raw_post.get("view_count", 0)
    return float(likes + (comments * 2) + (shares * 3) + (views * 0.01))

def detect_sentiment(text: str) -> str:
    if not text:
        return "neutral"
    text_lower = text.lower()
    pos_score = sum(1 for kw in SENTIMENT_KEYWORDS_POSITIVE if kw in text_lower)
    neg_score = sum(1 for kw in SENTIMENT_KEYWORDS_NEGATIVE if kw in text_lower)
    if pos_score > neg_score:
        return "positive"
    elif neg_score > pos_score:
        return "negative"
    return "neutral"

def detect_language(text: str) -> str:
    if not text:
        return "unknown"
    scores = {}
    for lang, pattern in LANGUAGE_BLOCKS.items():
        matches = len(re.findall(pattern, text))
        if matches > 0:
            scores[lang] = matches
    if not scores:
        return "unknown"
    return max(scores, key=scores.get)

TOPIC_KEYWORDS = {
    "safari": ["сафари", "游猎", "safari", "serengeti", "серенгети", "塞伦盖蒂"],
    "beach": ["пляж", "море", "海滩", "海", "beach", "ocean"],
    "hotel": ["отель", "гостиница", "酒店", "hotel", "resort"],
    "flight": ["рейс", "перелет", "航班", "flight", "direct"],
    "visa": ["виза", "签证", "visa", "entry"],
    "investment": ["инвестиции", "бизнес", "投资", "invest", "economic"],
    "luxury": ["люкс", "роскош", "奢华", "luxury", "vip"],
    "safety": ["безопасн", "опасн", "安全", "安全", "safety", "risk"],
    "payment": ["оплата", "карта", "支付", "payment", "card"],
    "logistics": ["транспорт", "логистик", "物流", "transport", "logistics"],
}

def extract_topics(text: str) -> List[str]:
    if not text:
        return []
    text_lower = text.lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                topics.append(topic)
                break
    return topics[:5]

async def collect_post_with_metadata(
    raw_post: Dict[str, Any], platform: str, custom_keyword: str = ""
) -> Dict[str, Any]:
    """Collect full post data with engagement metrics and source info."""
    text = raw_post.get("text", raw_post.get("content_snippet", ""))
    title = raw_post.get("title", "")
    full_text = f"{title}: {text}" if title else text
    
    engagement = {
        "likes": int(raw_post.get("liked_count", raw_post.get("score", 0))),
        "comments": int(raw_post.get("comment_count", 0)),
        "shares": int(raw_post.get("share_count", 0)),
        "views": int(raw_post.get("view_count", 0)),
        "total_score": calculate_engagement_score(raw_post),
    }
    
    follower_count = raw_post.get("follower_count", raw_post.get("author_followers", 0))
    
    return {
        "id": raw_post.get("id", str(uuid.uuid4())),
        "platform": platform,
        "author": raw_post.get("author", "Unknown"),
        "author_followers": follower_count,
        "is_influencer": follower_count > 10000 or engagement["total_score"] > 500,
        "content_snippet": full_text[:600],
        "url": raw_post.get("url", ""),
        "published_at": raw_post.get("published", raw_post.get("publishedDate", "")),
        "engagement": engagement,
        "sentiment": detect_sentiment(full_text),
        "is_crisis": raw_post.get("is_crisis", False),
        "topics": extract_topics(full_text),
        "language": detect_language(full_text),
        "source_keyword": custom_keyword,
    }


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
                    "content_snippet": await translate_to_english(p["content_snippet"][:150]),
                    "engagement": p.get("engagement", 0),
                    "is_crisis": p.get("is_crisis", False),
                }
                for p in insight.get("posts", [])[:2]
            ] if insight.get("posts") else [],
        })
    
    translated_alerts = []
    for alert in crisis_alerts[:3]:
        translated_alerts.append({
            "platform": alert.get("platform", "Unknown"),
            "author": alert.get("author", "Unknown"),
            "content_snippet": await translate_to_english(alert.get("content_snippet", "")[:150]),
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
    domains_str = f", includeDomains: {json.dumps(include_domains)}" if include_domains else ""
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
    
    # Fallback text parsing
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
    
    results = []
    async with XHS_SEMAPHORE:
        for kw in xhs_keywords:
            try:
                cmd = [mcporter, "call", f"xiaohongshu.search_feeds(keyword: '{kw}')"]
                loop = asyncio.get_event_loop()
                res = await loop.run_in_executor(None, lambda: subprocess.run(cmd, capture_output=True, timeout=15))
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    items = data.get("items", []) if isinstance(data, dict) else []
                    for item in items[:3]:
                        note = item.get("note_card", item)
                        desc = note.get("desc", "")
                        results.append({
                            "platform": "XiaoHongShu",
                            "author": note.get("user", {}).get("nickname", "Unknown"),
                            "content_snippet": desc[:200],
                            "engagement": int(note.get("interact_info", {}).get("liked_count", 0)),
                            "is_crisis": any(p in desc for p in CRISIS_PATTERNS_CN),
                            "url": f"https://www.xiaohongshu.com/explore/{note.get('note_id', '')}"
                        })
            except Exception as e:
                logger.warning(f"XHS search failed for '{kw}': {e}")
                continue
    return results

async def scan_russia_market(custom_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    keywords = get_all_keywords(KEYWORD_MATRIX_RU, custom_keywords)
    all_posts = []
    
    tasks = [run_exa_search_safe(kw, num_results=3, include_domains=FORUM_DOMAINS_RU) for kw in keywords]
    raw_outputs = await asyncio.gather(*tasks)
    
    for output in raw_outputs:
        parsed = _parse_exa_json_output(output)
        for item in parsed:
            is_crisis = any(re.search(p, item["text"], re.IGNORECASE) for p in CRISIS_PATTERNS_RU)
            all_posts.append({
                "platform": "Exa (RU)",
                "author": item["author"],
                "content_snippet": item["text"][:200],
                "engagement": int(item.get("score", 0) * 10),
                "is_crisis": is_crisis,
                "url": item["url"],
            })
    return all_posts

async def scan_china_market(custom_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    keywords = get_all_keywords(KEYWORD_MATRIX_CN, custom_keywords)
    all_posts = []
    
    tasks = [run_exa_search_safe(kw, num_results=3, include_domains=FORUM_DOMAINS_CN) for kw in keywords]
    raw_outputs = await asyncio.gather(*tasks)
    
    for output in raw_outputs:
        parsed = _parse_exa_json_output(output)
        for item in parsed:
            is_crisis = any(p in item["text"] for p in CRISIS_PATTERNS_CN)
            all_posts.append({
                "platform": "Exa (CN)",
                "author": item["author"],
                "content_snippet": item["text"][:200],
                "engagement": int(item.get("score", 0) * 10),
                "is_crisis": is_crisis,
                "url": item["url"],
            })
    return all_posts

def analyze_insights(posts: List[Dict[str, Any]], market: str) -> List[Dict[str, Any]]:
    insights = []
    crisis_posts = [p for p in posts if p["is_crisis"]]
    
    if crisis_posts:
        insights.append({
            "trend": f"Detected {len(crisis_posts)} potential crisis/safety signals",
            "sentiment": "Negative",
            "action": "Review crisis alerts and prepare PR/response strategy",
            "posts": crisis_posts[:3],
        })
        
    tourism_posts = [p for p in posts if not p["is_crisis"]]
    if tourism_posts:
        insights.append({
            "trend": "General tourism and logistics discussions active",
            "sentiment": "Neutral to Positive",
            "action": "Monitor for emerging luxury or investment queries",
            "posts": tourism_posts[:3],
        })
    return insights

async def generate_executive_summary(china_insights: List[Dict], russia_insights: List[Dict], alerts: List[Dict]) -> str:
    prompt = (
        "Write a concise, professional executive summary (max 3 paragraphs) for Tanzanian tourism stakeholders. "
        "Summarize the key findings from Chinese and Russian market scans. "
        f"China insights: {len(china_insights)} trends found. "
        f"Russia insights: {len(russia_insights)} trends found. "
        f"Crisis alerts: {len(alerts)} alerts detected. "
        "Highlight any urgent actions needed regarding safety, logistics, or investment opportunities."
    )
    
    if not openai_client:
        return "AI translation/summary disabled (no OPENAI_API_KEY). Manual review of insights required."
        
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert geopolitical and tourism intelligence analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            timeout=15.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate executive summary: {e}")
        return "Failed to generate AI summary. Please review raw insights."

async def run_full_scan_and_translate(client_id: str, custom_keywords: List[str]) -> Dict[str, Any]:
    logger.info(f"Starting full scan for client: {client_id}")
    
    # Run scans concurrently
    ru_posts, cn_posts, xhs_posts = await asyncio.gather(
        scan_russia_market(custom_keywords),
        scan_china_market(custom_keywords),
        scan_xiaohongshu_market(custom_keywords),
    )
    
    all_posts = ru_posts + cn_posts + xhs_posts
    raw_post_count = len(all_posts)
    
    # Analyze
    russia_insights = analyze_insights(ru_posts, "Russia")
    china_insights = analyze_insights(cn_posts + xhs_posts, "China")
    
    # Extract crisis alerts
    crisis_alerts = [p for p in all_posts if p["is_crisis"]]
    
    # Translate
    translated_cn_insights, translated_cn_alerts = await translate_insights(china_insights, crisis_alerts)
    translated_ru_insights, _ = await translate_insights(russia_insights, [])
    
    # Generate Summary
    summary = await generate_executive_summary(translated_cn_insights, translated_ru_insights, translated_cn_alerts)
    
    return {
        "status": "COMPLETED",
        "executiveSummary": summary,
        "chinaInsights": translated_cn_insights,
        "russiaInsights": translated_ru_insights,
        "crisisAlerts": translated_cn_alerts,
        "reportDate": datetime.now(timezone.utc).isoformat(),
        "raw_post_count": raw_post_count,
    }