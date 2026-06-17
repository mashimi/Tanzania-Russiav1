"""
Agent Reach Orchestration Layer -- ENHANCED INTELLIGENCE EDITION.
Features:
1. Full post content collection with metadata
2. Engagement metrics (likes, comments, shares, views)
3. Influencer detection (>10K followers)
4. Screenshot capture for archival
5. Translation toggle (original + English)
6. Trend analysis (vs historical average)
7. Action tracking (respond, flag, investigate, archive)
8. Time-range filtering support
9. Search and categorization
"""
import asyncio
import json
import os
import re
import shutil
import subprocess
import base64
from datetime import datetime, timezone, timedelta
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
EXA_SEMAPHORE = asyncio.Semaphore(5)
XHS_SEMAPHORE = asyncio.Semaphore(5)
SCREENSHOT_SEMAPHORE = asyncio.Semaphore(5)
TRANSLATE_SEMAPHORE = asyncio.Semaphore(5)

# -- Rich Post Metadata Helpers --

def calculate_engagement_score(post_data: dict) -> float:
    """Calculate weighted engagement score from likes, comments, shares."""
    likes = post_data.get("liked_count", post_data.get("likes", 0))
    comments = post_data.get("comment_count", post_data.get("comments", 0))
    shares = post_data.get("share_count", post_data.get("shares", 0))
    return float(likes * 1 + comments * 2 + shares * 3)

def detect_sentiment(text: str) -> str:
    """Simple keyword-based sentiment detection."""
    if not text or len(text) < 5:
        return "neutral"
    text_lower = text.lower()
    positive_words = ["good", "great", "excellent", "amazing", "beautiful", "love", "wonderful", "fantastic", "推荐", "不错", "很好", "отлично", "хорошо", "прекрасно"]
    negative_words = ["bad", "terrible", "awful", "horrible", "worst", "hate", "avoid", "dangerous", "避坑", "宰客", "诈骗", "危险", "ужасно", "плохо", "опасно", "мошен"]
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"

def extract_topics(text: str) -> List[str]:
    """Extect topics from post text using keyword matching."""
    topics = []
    if not text:
        return topics
    text_lower = text.lower()
    # Tourism
    if any(kw in text_lower for kw in ["сафари", "отдых", "туризм", "отель", "пляж", "旅游", "酒店", "度假", "游猎", "сафари", "safari", "hotel", "beach"]):
        topics.append("tourism")
    # Investment
    if any(kw in text_lower for kw in ["инвестиции", "экономика", "бизнес", "делегация", "投资", "经济", "商业", "合作", "investment", "economy", "business"]):
        topics.append("investment")
    # Logistics
    if any(kw in text_lower for kw in ["рейсы", "перелет", "виза", "билет", "маршрут", "签证", "航班", "机票", "物流", "flight", "visa", "ticket"]):
        topics.append("logistics")
    # Luxury
    if any(kw in text_lower for kw in ["роскошный", "люкс", "VIP", "премиум", "奢华", "高端", "豪华", "私人", "luxury", "premium", "exclusive"]):
        topics.append("luxury")
    # Crisis / Safety
    if any(kw in text_lower for kw in ["безопасн", "проблем", "мошен", "кризис", "安全", "危机", "诈骗", "危险", "安全", "safety", "crisis", "danger"]):
        topics.append("safety")
    if not topics:
        topics.append("general")
    return topics

def detect_language(text: str) -> str:
    """Quick language detection by character range."""
    if not text:
        return "unknown"
    # Check for Cyrillic characters (Russian)
    if re.search(r'[а-яА-ЯёЁ]', text):
        return "ru"
    # Check for CJK characters (Chinese)
    if re.search(r'[\u4e00-\u9fff]', text):
        return "zh"
    # Check for Latin characters (English)
    if re.match(r'^[A-Za-z0-9\s\.\,\!\?\-\:\;\(\).\'\"\/]+$', text):
        return "en"
    return "unknown"

async def collect_post_with_metadata(raw_post: dict, platform: str) -> Dict[str, Any]:
    """Collect full post data with engagement metrics and source info."""
    text = raw_post.get("text", raw_post.get("content", raw_post.get("content_snippet", "")))
    return {
        "platform": platform,
        "author": raw_post.get("author", "Unknown"),
        "author_followers": raw_post.get("author_followers", 0),
        "is_influencer": raw_post.get("author_followers", 0) > 10000 or raw_post.get("is_influencer", False),
        "content_original": text[:2000],
        "content_translated": "",
        "url": raw_post.get("url", ""),
        "published_at": raw_post.get("published", raw_post.get("published_at", raw_post.get("time", ""))),
        "engagement": int(raw_post.get("score", raw_post.get("engagement", 0))),
        "engagement_details": {
            "likes": raw_post.get("liked_count", raw_post.get("likes", 0)),
            "comments": raw_post.get("comment_count", raw_post.get("comments", 0)),
            "shares": raw_post.get("share_count", raw_post.get("shares", 0)),
            "views": raw_post.get("view_count", raw_post.get("views", 0)),
        },
        "sentiment": detect_sentiment(text),
        "is_crisis": raw_post.get("is_crisis", False) or any(p in text for p in CRISIS_PATTERNS_CN + CRISIS_PATTERNS_RU if isinstance(p, str)),
        "topics": extract_topics(text),
        "language": detect_language(text),
        "screenshot_url": raw_post.get("screenshot_url"),
        "trend_percentage": raw_post.get("trend_percentage", 0),
        "archived": raw_post.get("archived", False),
        "flagged": raw_post.get("flagged", False),
        "action_taken": raw_post.get("action_taken"),
    }

def detect_crisis_signal(text: str) -> bool:
    """Detect if text contains crisis/safety signals."""
    if not text:
        return False
    # Check CN patterns
    for p in CRISIS_PATTERNS_CN:
        if isinstance(p, str) and p in text:
            return True
    # Check RU patterns  
    for p in CRISIS_PATTERNS_RU:
        if isinstance(p, str):
            if re.search(p, text, re.IGNORECASE):
                return True
    return False

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

# -- Helper: Screenshot Capture --
async def capture_screenshot(url: str) -> Optional[str]:
    """Capture screenshot of a post URL using Playwright."""
    if not url or not url.startswith("http"):
        return None
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["python", "-m", "agent_reach.screenshot_capture", url],
                capture_output=True, timeout=30,
            ),
        )
        if result.returncode == 0:
            screenshot_data = result.stdout.decode("utf-8").strip()
            return screenshot_data if screenshot_data else None
    except Exception as e:
        logger.warning(f"Screenshot capture failed for {url}: {e}")
    return None

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

async def translate_insights(
    insights: List[Dict], crisis_alerts: List[Dict]
) -> Tuple[List[Dict], List[Dict]]:
    # Collect ALL translation tasks up front so they can run concurrently
    translation_tasks = []
    
    # Task tracker: maps (type, insight_idx, ...) -> result index
    trend_tasks = []
    action_tasks = []
    post_tasks = []
    alert_tasks = []
    
    for ii, insight in enumerate(insights):
        trend_tasks.append(translate_to_english(insight["trend"]))
        action_tasks.append(translate_to_english(insight["action"]))
        for p in insight.get("posts", [])[:5]:
            post_tasks.append(translate_to_english(p["content_snippet"][:300]))
    
    for alert in crisis_alerts[:5]:
        alert_tasks.append(translate_to_english(alert.get("content_snippet", "")[:300]))
    
    # Execute ALL translations concurrently
    trend_results = await asyncio.gather(*trend_tasks) if trend_tasks else []
    action_results = await asyncio.gather(*action_tasks) if action_tasks else []
    post_results = await asyncio.gather(*post_tasks) if post_tasks else []
    alert_results = await asyncio.gather(*alert_tasks) if alert_tasks else []
    
    # Rebuild translated insights from the batched results
    translated_insights = []
    post_idx = 0
    for ii, insight in enumerate(insights):
        posts = []
        for p in insight.get("posts", [])[:5]:
            translated_content = post_results[post_idx] if post_idx < len(post_results) else p["content_snippet"][:300]
            post_idx += 1
            posts.append({
                "platform": p["platform"],
                "author": p["author"],
                "author_followers": p.get("author_followers", 0),
                "is_influencer": p.get("is_influencer", False),
                "content_original": p.get("content_original", p["content_snippet"]),
                "content_translated": translated_content,
                "engagement": p.get("engagement", 0),
                "engagement_details": p.get("engagement_details", {
                    "likes": 0,
                    "comments": 0,
                    "shares": 0,
                    "views": 0,
                }),
                "is_crisis": p.get("is_crisis", False),
                "url": p.get("url", ""),
                "published_at": p.get("published_at", ""),
                "screenshot_url": p.get("screenshot_url"),
                "topics": p.get("topics", []),
                "language": p.get("language", "unknown"),
                "trend_percentage": p.get("trend_percentage", 0),
            })
        
        translated_insights.append({
            "trend": trend_results[ii] if ii < len(trend_results) else insight["trend"],
            "sentiment": insight["sentiment"],
            "action": action_results[ii] if ii < len(action_results) else insight["action"],
            "posts": posts if posts else [],
        })
    
    # Rebuild translated alerts
    translated_alerts = []
    for ai, alert in enumerate(crisis_alerts[:5]):
        translated_content = alert_results[ai] if ai < len(alert_results) else alert.get("content_snippet", "")[:300]
        translated_alerts.append({
            "platform": alert.get("platform", "Unknown"),
            "author": alert.get("author", "Unknown"),
            "author_followers": alert.get("author_followers", 0),
            "is_influencer": alert.get("is_influencer", False),
            "content_original": alert.get("content_original", alert.get("content_snippet", "")),
            "content_translated": translated_content,
            "engagement": alert.get("engagement", 0),
            "engagement_details": alert.get("engagement_details", {
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "views": 0,
            }),
            "is_crisis": True,
            "url": alert.get("url", ""),
            "published_at": alert.get("published_at", ""),
            "screenshot_url": alert.get("screenshot_url"),
            "topics": alert.get("topics", []),
            "language": alert.get("language", "unknown"),
            "trend_percentage": alert.get("trend_percentage", 0),
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

async def _search_xhs_keyword(kw: str) -> List[Dict[str, Any]]:
    """Search a single XHS keyword and return posts with concurrent screenshots."""
    mcporter = _get_mcporter_path()
    if not mcporter:
        return []
    
    results = []
    try:
        cmd = [mcporter, "call", f"xiaohongshu.search_feeds(keyword: '{kw}')"]
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: subprocess.run(cmd, capture_output=True, timeout=15))
        if res.returncode == 0:
            data = json.loads(res.stdout)
            items = data.get("items", []) if isinstance(data, dict) else []
            
            # Parse items first
            raw_items = []
            for item in items[:3]:
                note = item.get("note_card", item)
                desc = note.get("desc", "")
                user = note.get("user", {})
                interact = note.get("interact_info", {})
                note_url = f"https://www.xiaohongshu.com/explore/{note.get('note_id', '')}"
                raw_items.append({
                    "desc": desc,
                    "user": user,
                    "interact": interact,
                    "note_url": note_url,
                })
            
            # Batch screenshots concurrently
            async def enrich_xhs(item: dict) -> dict:
                async with SCREENSHOT_SEMAPHORE:
                    screenshot = await capture_screenshot(item["note_url"])
                return {
                    "platform": "XiaoHongShu",
                    "author": item["user"].get("nickname", "Unknown"),
                    "author_followers": int(item["user"].get("follower_count", 0)),
                    "is_influencer": int(item["user"].get("follower_count", 0)) > 10000,
                    "content_original": item["desc"][:500],
                    "content_snippet": item["desc"][:200],
                    "engagement": int(item["interact"].get("liked_count", 0)),
                    "engagement_details": {
                        "likes": int(item["interact"].get("liked_count", 0)),
                        "comments": int(item["interact"].get("comment_count", 0)),
                        "shares": int(item["interact"].get("share_count", 0)),
                        "views": 0,
                    },
                    "is_crisis": any(p in item["desc"] for p in CRISIS_PATTERNS_CN),
                    "url": item["note_url"],
                    "published_at": item.get("time", ""),
                    "screenshot_url": screenshot,
                    "topics": ["tourism"] if "旅游" in item["desc"] else ["general"],
                    "language": "zh",
                    "trend_percentage": 0,
                }
            
            if raw_items:
                posts = await asyncio.gather(*[enrich_xhs(item) for item in raw_items])
                results.extend(posts)
    except Exception as e:
        logger.warning(f"XHS search failed for '{kw}': {e}")
    return results

async def scan_xiaohongshu_market(
    custom_keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    xhs_keywords = [
        "Tanzania lv you",
        "Sanggeiba er gong lue",
        "Tanzania bi keng",
        "Fei zhou you lie",
    ] + (custom_keywords or [])
    
    # Run ALL keyword searches CONCURRENTLY with semaphore control
    async def limited_search(kw: str) -> List[Dict[str, Any]]:
        async with XHS_SEMAPHORE:
            return await _search_xhs_keyword(kw)
    
    results_lists = await asyncio.gather(*[limited_search(kw) for kw in xhs_keywords])
    results = []
    for rl in results_lists:
        results.extend(rl)
    return results

async def scan_russia_market(custom_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    keywords = get_all_keywords(KEYWORD_MATRIX_RU, custom_keywords)
    all_posts = []
    
    tasks = [run_exa_search_safe(kw, num_results=3, include_domains=FORUM_DOMAINS_RU) for kw in keywords]
    raw_outputs = await asyncio.gather(*tasks)
    
    # Parse all items first
    parsed_items = []
    for output in raw_outputs:
        parsed = _parse_exa_json_output(output)
        parsed_items.extend(parsed)
    
    # Batch all screenshots CONCURRENTLY instead of serial
    async def enrich_post(item: dict) -> dict:
        is_crisis = any(re.search(p, item["text"], re.IGNORECASE) for p in CRISIS_PATTERNS_RU)
        async with SCREENSHOT_SEMAPHORE:
            screenshot = await capture_screenshot(item["url"])
        return {
            "platform": "Exa (RU)",
            "author": item["author"],
            "author_followers": 0,
            "is_influencer": False,
            "content_original": item["text"][:500],
            "content_snippet": item["text"][:200],
            "engagement": int(item.get("score", 0) * 10),
            "engagement_details": {
                "likes": int(item.get("score", 0) * 10),
                "comments": 0,
                "shares": 0,
                "views": 0,
            },
            "is_crisis": is_crisis,
            "url": item["url"],
            "published_at": item.get("published", ""),
            "screenshot_url": screenshot,
            "topics": ["investment"] if "инвести" in item["text"].lower() else ["tourism"],
            "language": "ru",
            "trend_percentage": 0,
        }
    
    if parsed_items:
        posts = await asyncio.gather(*[enrich_post(item) for item in parsed_items])
        all_posts.extend(posts)
    return all_posts

async def scan_china_market(custom_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    keywords = get_all_keywords(KEYWORD_MATRIX_CN, custom_keywords)
    all_posts = []
    
    tasks = [run_exa_search_safe(kw, num_results=3, include_domains=FORUM_DOMAINS_CN) for kw in keywords]
    raw_outputs = await asyncio.gather(*tasks)
    
    # Parse all items first
    parsed_items = []
    for output in raw_outputs:
        parsed = _parse_exa_json_output(output)
        parsed_items.extend(parsed)
    
    # Batch all screenshots CONCURRENTLY instead of serial
    async def enrich_post(item: dict) -> dict:
        is_crisis = any(p in item["text"] for p in CRISIS_PATTERNS_CN)
        async with SCREENSHOT_SEMAPHORE:
            screenshot = await capture_screenshot(item["url"])
        return {
            "platform": "Exa (CN)",
            "author": item["author"],
            "author_followers": 0,
            "is_influencer": False,
            "content_original": item["text"][:500],
            "content_snippet": item["text"][:200],
            "engagement": int(item.get("score", 0) * 10),
            "engagement_details": {
                "likes": int(item.get("score", 0) * 10),
                "comments": 0,
                "shares": 0,
                "views": 0,
            },
            "is_crisis": is_crisis,
            "url": item["url"],
            "published_at": item.get("published", ""),
            "screenshot_url": screenshot,
            "topics": ["investment"] if "投资" in item["text"] else ["tourism"],
            "language": "zh",
            "trend_percentage": 0,
        }
    
    if parsed_items:
        posts = await asyncio.gather(*[enrich_post(item) for item in parsed_items])
        all_posts.extend(posts)
    return all_posts

def analyze_insights(posts: List[Dict[str, Any]], market: str) -> List[Dict[str, Any]]:
    insights = []
    crisis_posts = [p for p in posts if p["is_crisis"]]
    
    if crisis_posts:
        insights.append({
            "trend": f"Detected {len(crisis_posts)} potential crisis/safety signals",
            "sentiment": "Negative",
            "action": "Review crisis alerts and prepare PR/response strategy",
            "posts": crisis_posts[:5],
        })
        
    tourism_posts = [p for p in posts if not p["is_crisis"]]
    if tourism_posts:
        insights.append({
            "trend": "General tourism and logistics discussions active",
            "sentiment": "Neutral to Positive",
            "action": "Monitor for emerging luxury or investment queries",
            "posts": tourism_posts[:5],
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
    logger.info(f"Starting full enhanced scan for client: {client_id}")
    
    ru_posts, cn_posts, xhs_posts = await asyncio.gather(
        scan_russia_market(custom_keywords),
        scan_china_market(custom_keywords),
        scan_xiaohongshu_market(custom_keywords),
    )
    
    all_posts = ru_posts + cn_posts + xhs_posts
    raw_post_count = len(all_posts)
    
    russia_insights = analyze_insights(ru_posts, "Russia")
    china_insights = analyze_insights(cn_posts + xhs_posts, "China")
    
    crisis_alerts = [p for p in all_posts if p["is_crisis"]]
    
    translated_cn_insights, translated_cn_alerts = await translate_insights(china_insights, crisis_alerts)
    translated_ru_insights, _ = await translate_insights(russia_insights, [])
    
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


