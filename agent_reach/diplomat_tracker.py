# -*- coding: utf-8 -*-
"""
Diplomatic Impact Tracker — Agent Reach plugin.

Monitors geopolitical events for diplomatic "tailwinds" that create
tourism, investment, and trade opportunities. Tracks surge in digital
sentiment from Russian, Chinese, and international sources following
Head-of-State diplomatic visits.

Usage:
    from agent_reach.diplomat_tracker import DiplomatTracker

    tracker = DiplomatTracker()
    report = tracker.generate_report()  # returns dict with findings
    print(tracker.report_to_text(report))

Configuration via config.yaml:
    diplomat_tracker.diplomacy_keywords_russia  (list)
    diplomat_tracker.diplomacy_keywords_china   (list)
    diplomat_tracker.diplomacy_keywords_global  (list)
    diplomat_tracker.alert_threshold            (float, default=2.0)
    diplomat_tracker.history_days               (int, default=60)
"""

import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_reach.config import Config

# ── Default diplomatic keyword sets ───────────────────────────────────────

DIPLOMACY_KEYWORDS_RU: List[str] = [
    "Танзания инвестиции 2026",        # Tanzania investments 2026
    "прямые рейсы Танзания",           # Direct flights Tanzania
    "Танзания Самия Сулуху Хассан",    # Tanzania Samia Suluhu Hassan
    "Занзибар бизнес делегация",       # Zanzibar business delegation
    "Танзания Россия экономика",       # Tanzania Russia economy
    "Танзания туризм партнёрство",     # Tanzania tourism partnership
    "Африка бизнес форум",             # Africa business forum (catch-all)
    "Занзибар инвестиции",             # Zanzibar investments
    "Дарес Салам деловая миссия",      # Dar es Salaam business mission
    "российские туристы Танзания",     # Russian tourists Tanzania
    "Танзания виза новости",           # Tanzania visa news
    "Серенгети бизнес",                # Serengeti business
]

DIPLOMACY_KEYWORDS_CN: List[str] = [
    "坦桑尼亚 投资 机遇",              # Tanzania investment opportunities
    "中坦 旅游 合作",                  # China-Tanzania tourism cooperation
    "坦桑尼亚 总统 经济",              # Tanzania President economy
    "桑给巴尔 商务 考察",              # Zanzibar business inspection/tour
    "坦桑尼亚 一带一路",              # Tanzania Belt and Road
    "坦桑尼亚 签证 政策",              # Tanzania visa policy
    "坦桑尼亚 直飞 航班",              # Tanzania direct flights
    "坦桑尼亚 矿业 合作",              # Tanzania mining cooperation
    "坦桑尼亚 农业 投资",              # Tanzania agriculture investment
    "坦桑尼亚 房地产 投资",            # Tanzania real estate investment
    "中坦 经贸 合作",                  # China-Tanzania economic cooperation
    "坦桑尼亚 商务 考察 团",           # Tanzania business delegation
]

DIPLOMACY_KEYWORDS_GLOBAL: List[str] = [
    "Tanzania investment opportunities",
    "Tanzania Russia relations",
    "Tanzania China Belt and Road",
    "Samia Suluhu Hassan economic diplomacy",
    "Tanzania tourism boom",
    "Zanzibar luxury real estate",
    "Dar es Salaam business hub",
    "Tanzania mining sector",
    "Tanzania agriculture investment",
    "Serengeti tourism growth",
    "Tanzania infrastructure projects",
    "Tanzania trade delegation",
]

# ── Platform detection patterns ──────────────────────────────────────────

PLATFORM_PATTERNS: Dict[str, List[str]] = {
    "xiaohongshu": [r"xiaohongshu", r"xhslink", r"xhs\.cn", r"redbook"],
    "weibo": [r"weibo\.com", r"weibo\.cn"],
    "bilibili": [r"bilibili\.com", r"b23\.tv"],
    "wechat": [r"mp\.weixin\.qq", r"weixin\.qq"],
    "douyin": [r"douyin\.com", r"iesdouyin"],
    "zhihu": [r"zhihu\.com"],
    "vk": [r"vk\.com", r"vkontakte"],
    "yandex": [r"yandex\.ru", r"ya\.ru"],
    "awd": [r"awd\.ru"],
    "reddit": [r"reddit\.com"],
    "youtube": [r"youtube\.com", r"youtu\.be"],
    "twitter": [r"twitter\.com", r"x\.com"],
    "linkedin": [r"linkedin\.com"],
}

# ── Default travel forum URLs (for direct scraping targets) ──────────────

FORUM_TARGETS: Dict[str, List[str]] = {
    "awd.ru": [
        "https://www.awd.ru/tanzania/",
        "https://www.awd.ru/zanzibar/",
    ],
    "pikabu.ru": [
        "https://pikabu.ru/tag/Танзания",
        "https://pikabu.ru/tag/Занзибар",
    ],
    "bilibili": [
        "https://search.bilibili.com/all?keyword=坦桑尼亚旅游",
        "https://search.bilibili.com/all?keyword=桑给巴尔攻略",
    ],
    "xiaohongshu": [
        "https://www.xiaohongshu.com/search_result?keyword=坦桑尼亚投资",
        "https://www.xiaohongshu.com/search_result?keyword=桑给巴尔旅游",
    ],
    "weibo": [
        "https://s.weibo.com/weibo?q=坦桑尼亚 投资",
        "https://s.weibo.com/weibo?q=桑给巴尔 旅游",
    ],
}


class DiplomatTracker:
    """Track diplomatic-impact signals across Russian, Chinese, and global sources."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.data_dir = Path.home() / ".agent-reach" / "diplomacy"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load custom keywords from config if present
        self.keywords_ru = (
            self.config.get("diplomacy_keywords_russia") or DIPLOMACY_KEYWORDS_RU
        )
        self.keywords_cn = (
            self.config.get("diplomacy_keywords_china") or DIPLOMACY_KEYWORDS_CN
        )
        self.keywords_global = (
            self.config.get("diplomacy_keywords_global") or DIPLOMACY_KEYWORDS_GLOBAL
        )

        self.alert_threshold = float(self.config.get("diplomacy_alert_threshold", 2.0))
        self.history_days = int(self.config.get("diplomacy_history_days", 60))

        # Baseline counts (loaded from history)
        self.baseline: Dict[str, Dict[str, int]] = self._load_baseline()

    # ── Persistence ──────────────────────────────────────────────────────

    def _baseline_path(self) -> Path:
        return self.data_dir / "baseline.json"

    def _load_baseline(self) -> Dict[str, Dict[str, int]]:
        path = self._baseline_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_baseline(self):
        path = self._baseline_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.baseline, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ── Keyword-based search helper (simulated / via Exa) ──────────────────

    def search_keyword(self, keyword: str, source: str = "exa") -> Dict[str, Any]:
        """Search a keyword using available channels.

        Currently uses local simulation. In production, this would call
        Exa MCP, mcporter, or platform-specific CLI tools (bili-cli, xhs-cli, etc.)
        Returns a dict with:
            - count: int (approximate mention count)
            - sources: list of str (source names)
            - platform: list of str (platform names where found)
        """
        # Placeholder: actual scraping would plug into Exa MCP here.
        # For MVP, return a structured result indicating the keyword is ready.
        return {
            "keyword": keyword,
            "count": 0,
            "sources": [],
            "platform": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def search_keywords_batch(
        self, keywords: List[str], source: str = "exa"
    ) -> List[Dict[str, Any]]:
        """Run search_keyword for a list of keywords."""
        return [self.search_keyword(kw, source) for kw in keywords]

    # ── Baseline management ───────────────────────────────────────────────

    def update_baseline(self, results: Dict[str, List[Dict[str, Any]]]):
        """Update stored baseline counts from latest search results."""
        for lang, keyword_results in results.items():
            if lang not in self.baseline:
                self.baseline[lang] = {}
            for r in keyword_results:
                self.baseline[lang][r["keyword"]] = r.get("count", 0)
        self._save_baseline()

    def detect_surge(
        self, current: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Compare current counts to baseline and return alerts for surges.

        An alert is triggered when a keyword's mention count exceeds
        `alert_threshold` times the baseline (or baseline+1 to avoid div/0).
        """
        alerts = []
        for lang, keyword_results in current.items():
            baseline_lang = self.baseline.get(lang, {})
            for r in keyword_results:
                kw = r["keyword"]
                current_count = r.get("count", 0)
                prev_count = baseline_lang.get(kw, 0)
                # +1 to avoid division by zero
                ratio = current_count / (prev_count + 1)
                if ratio >= self.alert_threshold:
                    platform_list = r.get("platform", [])
                    alerts.append({
                        "keyword": kw,
                        "language": lang,
                        "current_count": current_count,
                        "previous_count": prev_count,
                        "ratio": round(ratio, 2),
                        "platforms": platform_list,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "severity": (
                            "CRITICAL" if ratio >= 5.0
                            else "HIGH" if ratio >= 3.0
                            else "MEDIUM"
                        ),
                    })
        return alerts

    # ── Sentiment & Interest Analysis ────────────────────────────────────

    def analyze_interest_themes(
        self, alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Derive actionable themes from detected alerts.

        Maps keywords to strategic recommendations.
        """
        themes = []
        alert_keywords = {a["keyword"].lower() for a in alerts}

        # Russia interest mapping
        ru_investment = any(
            kw in alert_keywords
            for kw in ["Танзания инвестиции 2026", "Занзибар инвестиции"]
        )
        ru_flights = any(
            kw in alert_keywords
            for kw in ["прямые рейсы Танзания"]
        )
        ru_tourism = any(
            kw in alert_keywords
            for kw in [
                "российские туристы Танзания",
                "Танзания туризм партнёрство",
            ]
        )

        # China interest mapping
        cn_investment = any(
            kw in alert_keywords
            for kw in ["坦桑尼亚 投资 机遇", "中坦 经贸 合作"]
        )
        cn_tourism = any(
            kw in alert_keywords
            for kw in ["中坦 旅游 合作", "坦桑尼亚 直飞 航班"]
        )
        cn_visa = any(
            kw in alert_keywords
            for kw in ["坦桑尼亚 签证 政策"]
        )

        # Global interest mapping
        global_investment = any(
            kw in alert_keywords
            for kw in ["Tanzania investment opportunities", "Tanzania mining sector"]
        )
        global_luxury = any(
            kw in alert_keywords
            for kw in ["Zanzibar luxury real estate", "Serengeti tourism growth"]
        )

        # Build recommendations
        if ru_investment:
            themes.append(
                "Russian investors showing interest — prepare Russian-language "
                "investment brochures and contact TIC (Tanzania Investment Centre)"
            )
        if ru_flights:
            themes.append(
                "Russian flight demand detected — engage with airlines (Aeroflot, "
                "Nordwind) and airports for charter/direct route discussions"
            )
        if ru_tourism:
            themes.append(
                "Russian tourist surge — update Russian-language landing pages, "
                "train staff in basic Russian, partner with Russian tour operators"
            )
        if cn_investment:
            themes.append(
                "Chinese investment interest detected — publish Mandarin case "
                "studies on WeChat Official Accounts, attend China-Africa forums"
            )
        if cn_tourism:
            themes.append(
                "Chinese tourism demand rising — activate Douyin/TikTok campaigns, "
                "invite Chinese KOLs for familiarization trips"
            )
        if cn_visa:
            themes.append(
                "Visa policy queries from China — ensure visa-on-arrival info "
                "is prominently displayed on Chinese social media"
            )
        if global_investment:
            themes.append(
                "Global investment attention — prepare for mining/agriculture "
                "delegations, update English-language pitch decks"
            )
        if global_luxury:
            themes.append(
                "Luxury tourism segment growing — target high-net-worth travelers "
                "with exclusive Serengeti/Zanzibar packages"
            )

        if not themes:
            themes.append(
                "No significant diplomatic signal detected yet — continue "
                "monitoring; consider broadening keyword scope"
            )

        return themes

    # ── Report Generation ────────────────────────────────────────────────

    def generate_report(
        self, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Generate a complete Diplomatic Dividend report.

        Returns a structured dict with:
            - meta: report metadata (timestamp, period, threshold)
            - keywords: keyword sets by language
            - alerts: detected surges (empty if using simulated search)
            - themes: actionable insights derived from alerts
            - recommendations: strategic next steps
        """
        # Run keyword searches
        ru_results = self.search_keywords_batch(self.keywords_ru)
        cn_results = self.search_keywords_batch(self.keywords_cn)
        global_results = self.search_keywords_batch(self.keywords_global)

        current = {
            "russian": ru_results,
            "chinese": cn_results,
            "global": global_results,
        }

        # Detect surges vs baseline
        alerts = self.detect_surge(current)

        # Derive themes
        themes = self.analyze_interest_themes(alerts)

        # Update baseline for next comparison
        self.update_baseline(current)

        report = {
            "meta": {
                "report_title": "The Diplomatic Dividend",
                "subtitle": "What Russia & China Are Saying About Tanzania This Week",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "period_days": self.history_days,
                "alert_threshold": self.alert_threshold,
                "total_keywords_tracked": (
                    len(self.keywords_ru)
                    + len(self.keywords_cn)
                    + len(self.keywords_global)
                ),
                "keywords_russia": len(self.keywords_ru),
                "keywords_china": len(self.keywords_cn),
                "keywords_global": len(self.keywords_global),
            },
            "keywords": {
                "russian": self.keywords_ru,
                "chinese": self.keywords_cn,
                "global": self.keywords_global,
            },
            "search_results": {
                "russian": ru_results,
                "chinese": cn_results,
                "global": global_results,
            },
            "alerts": alerts,
            "alert_count": len(alerts),
            "themes": themes,
            "recommendations": self._generate_recommendations(alerts, themes),
        }

        # Save report to disk
        self._save_report(report)

        return report

    def _generate_recommendations(
        self, alerts: List[Dict[str, Any]], themes: List[str]
    ) -> List[str]:
        """Generate concrete business recommendations."""
        recs = []

        # Determine which languages have activity
        has_ru = any(a["language"] == "russian" for a in alerts)
        has_cn = any(a["language"] == "chinese" for a in alerts)
        has_global = any(a["language"] == "global" for a in alerts)

        if has_ru or "Russian" in str(themes):
            recs.append(
                "IMMEDIATE: Update Russian-language website and booking pages. "
                "The diplomatic tailwind from the President's Russia trip is "
                "active — capture this search traffic now."
            )
            recs.append(
                "SHORT-TERM: Partner with Russian tour operators (Coral Travel, "
                "Pegas Touristik) to package Tanzania as a new destination."
            )

        if has_cn or "Chinese" in str(themes):
            recs.append(
                "IMMEDIATE: Publish Chinese-language content on WeChat Official "
                "Accounts and XiaoHongShu highlighting visa-on-arrival and "
                "direct flight options."
            )
            recs.append(
                "SHORT-TERM: Invite 5-10 Chinese travel KOLs for a familiarization "
                "trip to Zanzibar and Serengeti — content will generate "
                "compounding organic interest."
            )

        if has_global:
            recs.append(
                "SHORT-TERM: Issue a press release highlighting Tanzania's "
                "investment climate following the diplomatic mission — target "
                "Bloomberg, Reuters, and CNBC Africa."
            )

        if not recs:
            recs.append(
                "MONITOR: Continue daily tracking. Keywords are loaded and "
                "ready — run 'agent-reach diplomacy scan' to force a full "
                "search cycle against Exa and platform-specific channels."
            )

        return recs

    def _save_report(self, report: Dict[str, Any]):
        """Save report JSON to data directory."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = self.data_dir / f"report_{timestamp}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def list_reports(self) -> List[Dict[str, str]]:
        """List all generated reports with timestamps."""
        reports = []
        for f in sorted(self.data_dir.glob("report_*.json"), reverse=True):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                reports.append({
                    "file": f.name,
                    "generated_at": data.get("meta", {}).get("generated_at", ""),
                    "alert_count": data.get("alert_count", 0),
                    "themes_count": len(data.get("themes", [])),
                })
            except (json.JSONDecodeError, OSError):
                pass
        return reports

    # ── Text Formatting ──────────────────────────────────────────────────

    def report_to_text(self, report: Dict[str, Any]) -> str:
        """Format the report as a human-readable text string."""
        meta = report.get("meta", {})
        lines = []
        lines.append("=" * 66)
        lines.append(f"  {meta.get('report_title', 'The Diplomatic Dividend')}")
        lines.append(f"  {meta.get('subtitle', '')}")
        lines.append("=" * 66)
        lines.append(f"  Generated: {meta.get('generated_at', 'N/A')}")
        lines.append(
            f"  Keywords tracked: {meta.get('total_keywords_tracked', 0)} "
            f"(RU:{meta.get('keywords_russia', 0)}, "
            f"CN:{meta.get('keywords_china', 0)}, "
            f"EN:{meta.get('keywords_global', 0)})"
        )
        lines.append(f"  Alert threshold: {meta.get('alert_threshold', 2.0)}x baseline")
        lines.append("")

        # Alerts section
        alerts = report.get("alerts", [])
        lines.append(f"📊 ALERTS DETECTED: {len(alerts)}")
        lines.append("-" * 66)
        if alerts:
            for a in alerts:
                lines.append(
                    f"  [{a['severity']:>8}] {a['keyword']} "
                    f"(ratio: {a['ratio']}x, lang: {a['language']})"
                )
        else:
            lines.append("  No surges detected yet. Keywords are primed and monitoring.")
        lines.append("")

        # Themes section
        themes = report.get("themes", [])
        lines.append(f"🎯 ACTIONABLE THEMES: {len(themes)}")
        lines.append("-" * 66)
        for i, theme in enumerate(themes, 1):
            lines.append(f"  {i}. {theme}")
        lines.append("")

        # Recommendations
        recs = report.get("recommendations", [])
        lines.append(f"⚡ STRATEGIC RECOMMENDATIONS: {len(recs)}")
        lines.append("-" * 66)
        for i, rec in enumerate(recs, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")
        lines.append("=" * 66)
        lines.append("  Powered by Agent Reach — Geopolitical Tourism Radar")
        lines.append("=" * 66)

        return "\n".join(lines)

    def report_to_pdf_text(self, report: Dict[str, Any]) -> str:
        """Format the report as a clean 1-page text suitable for PDF generation.

        This is the 'Special Report' format — concise, executive-ready.
        """
        meta = report.get("meta", {})
        alerts = report.get("alerts", [])
        themes = report.get("themes", [])
        recs = report.get("recommendations", [])

        lines = []
        lines.append("╔══════════════════════════════════════════════════════════════════╗")
        lines.append("║            THE DIPLOMATIC DIVIDEND — SPECIAL REPORT             ║")
        lines.append("║  What Russia & China Are Saying About Tanzania This Week        ║")
        lines.append("╚══════════════════════════════════════════════════════════════════╝")
        lines.append("")
        lines.append(f"Report Date: {meta.get('generated_at', 'N/A')}")
        lines.append(f"Keywords Tracked: {meta.get('total_keywords_tracked', 0)}")
        lines.append("")

        # Executive summary
        if alerts:
            lines.append("EXECUTIVE SUMMARY")
            lines.append("-" * 60)
            lines.append(
                f"We have detected {len(alerts)} significant surge(s) in "
                f"diplomatic and tourism-related keyword mentions. "
                f"This indicates the President's economic mission is generating "
                f"measurable foreign interest."
            )
        else:
            lines.append("EXECUTIVE SUMMARY")
            lines.append("-" * 60)
            lines.append(
                "Monitoring is active. Keywords are loaded across Russian, "
                "Chinese, and global sources. No surges yet — system is "
                "building baseline for delta detection."
            )
        lines.append("")

        # Key findings
        if themes:
            lines.append("KEY FINDINGS & INSIGHTS")
            lines.append("-" * 60)
            for i, theme in enumerate(themes, 1):
                lines.append(f"  • {theme}")
            lines.append("")

        # Recommendations
        if recs:
            lines.append("STRATEGIC RECOMMENDATIONS")
            lines.append("-" * 60)
            for i, rec in enumerate(recs, 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")

        lines.append("─" * 60)
        lines.append("Generated by Agent Reach — Geopolitical Tourism Radar")
        lines.append("Contact: https://github.com/Panniantong/Agent-Reach")
        lines.append("─" * 60)

        return "\n".join(lines)


# ── Convenience functions ────────────────────────────────────────────────

def run_diplomacy_scan() -> Dict[str, Any]:
    """Run a full diplomacy scan and return the report."""
    tracker = DiplomatTracker()
    return tracker.generate_report()


def get_latest_report() -> Optional[Dict[str, Any]]:
    """Get the most recent saved report, if any."""
    tracker = DiplomatTracker()
    reports = tracker.list_reports()
    if not reports:
        return None
    latest = reports[0]
    path = tracker.data_dir / latest["file"]
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def keyword_sets() -> Dict[str, List[str]]:
    """Return the default diplomatic keyword sets for reference."""
    return {
        "russian": DIPLOMACY_KEYWORDS_RU,
        "chinese": DIPLOMACY_KEYWORDS_CN,
        "global": DIPLOMACY_KEYWORDS_GLOBAL,
    }