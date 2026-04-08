"""
KairosAI — Tool: sentiment_analyzer
--------------------------------------
Analyses user feedback entries to produce:
  - Overall sentiment score (-1.0 to +1.0)
  - Sentiment distribution
  - Repeated issue themes with frequency counts
  - High-severity signals (churn, payment, crash)
  - Per-channel and per-tier breakdowns
  - Representative quotes per theme

NOTE: This is a rule-based analyser (no LLM call needed here — agents
will interpret the structured output). It uses keyword matching and
the pre-tagged sentiment/feature fields from feedback.py.

Called by: Marketing/Comms Agent, PM Agent, War Room Monitor
"""

from typing import TypedDict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.feedback import get_all, get_by_sentiment, get_summary_stats


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------

class ThemeSummary(TypedDict):
    theme: str
    count: int
    sentiment_breakdown: dict[str, int]   # positive/neutral/negative counts
    severity: str                          # "critical" | "high" | "medium" | "low"
    representative_quotes: list[str]       # up to 2 example texts


class SentimentReport(TypedDict):
    overall_score: float                   # -1.0 (all negative) to +1.0 (all positive)
    total_entries: int
    distribution: dict[str, int]           # positive/neutral/negative counts
    distribution_pct: dict[str, float]     # as percentages
    dominant_sentiment: str
    critical_signals: list[str]            # e.g. ["churn_risk", "payment_failure", "crash_epidemic"]
    themes: list[ThemeSummary]
    channel_breakdown: dict[str, dict]     # per-source sentiment summary
    tier_breakdown: dict[str, dict]        # per-user-tier sentiment summary
    enterprise_negative_pct: float         # % of enterprise feedback that is negative (high impact)
    verbatim_highlights: dict[str, list[str]]  # "most_negative", "most_positive" quotes


# ---------------------------------------------------------------------------
# Theme definitions — maps feature_tag groups to human labels + severity
# ---------------------------------------------------------------------------

THEME_DEFINITIONS = {
    "crash": {
        "label": "App crashes & freezes",
        "severity": "critical",
        "tags": ["crash"],
    },
    "performance": {
        "label": "Slowness & latency degradation",
        "severity": "high",
        "tags": ["performance"],
    },
    "payment": {
        "label": "Payment failures & billing errors",
        "severity": "critical",
        "tags": ["payment"],
    },
    "data_integrity": {
        "label": "Data loss, sync, & migration issues",
        "severity": "high",
        "tags": ["data_migration", "data_integrity", "data_sync"],
    },
    "churn_risk": {
        "label": "Cancellation & churn signals",
        "severity": "critical",
        "tags": ["churn_signal"],
    },
    "smart_dashboard": {
        "label": "SmartDash 2.0 UX & feature reception",
        "severity": "medium",
        "tags": ["smart_dashboard", "analytics_view", "ai_summary"],
    },
    "platform": {
        "label": "Cross-platform & stability",
        "severity": "medium",
        "tags": ["cross_platform", "stability", "access_control"],
    },
    "positive_reception": {
        "label": "Positive feature feedback",
        "severity": "low",
        "tags": ["collaborative_notes", "accessibility"],
    },
}

CRITICAL_SIGNAL_RULES = {
    "churn_epidemic": lambda themes: _theme_count(themes, "churn_risk") >= 2,
    "crash_epidemic": lambda themes: _theme_count(themes, "crash") >= 4,
    "payment_failure_spike": lambda themes: _theme_count(themes, "payment") >= 2,
    "data_loss_reported": lambda themes: _theme_count(themes, "data_integrity") >= 2,
    "enterprise_at_risk": lambda _, tier_data: (
        tier_data.get("enterprise", {}).get("negative_pct", 0) >= 40
    ),
}


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def sentiment_analyzer(
    include_quotes: bool = True,
    max_quotes_per_theme: int = 2,
) -> SentimentReport:
    """
    Run sentiment analysis on all feedback entries.

    Args:
        include_quotes: Whether to include representative quotes.
        max_quotes_per_theme: Max verbatim examples per theme.

    Returns:
        SentimentReport with full breakdown.
    """
    all_feedback = get_all()
    stats = get_summary_stats()

    total = stats["total"]
    dist = stats["by_sentiment"]

    # Overall sentiment score: +1 per positive, -1 per negative, 0 for neutral
    score = (dist["positive"] - dist["negative"]) / total if total > 0 else 0.0
    score = round(score, 3)

    dominant = max(dist, key=lambda k: dist[k])

    # ------------------------------------------------------------------
    # Theme analysis
    # ------------------------------------------------------------------
    themes: list[ThemeSummary] = []

    for theme_key, theme_def in THEME_DEFINITIONS.items():
        matching = [
            f for f in all_feedback
            if f["feature_tag"] in theme_def["tags"]
        ]
        if not matching:
            continue

        sentiment_breakdown = {"positive": 0, "neutral": 0, "negative": 0}
        for entry in matching:
            sentiment_breakdown[entry["sentiment"]] += 1

        quotes = []
        if include_quotes:
            # Prefer negative quotes for critical themes, positive for positive themes
            preferred = "negative" if theme_def["severity"] in ("critical", "high") else "positive"
            preferred_entries = [e for e in matching if e["sentiment"] == preferred]
            fallback_entries = [e for e in matching if e["sentiment"] != preferred]
            candidates = preferred_entries + fallback_entries
            quotes = [e["text"][:120] + "..." if len(e["text"]) > 120 else e["text"]
                      for e in candidates[:max_quotes_per_theme]]

        themes.append(ThemeSummary(
            theme=theme_def["label"],
            count=len(matching),
            sentiment_breakdown=sentiment_breakdown,
            severity=theme_def["severity"],
            representative_quotes=quotes,
        ))

    # Sort themes by severity then count
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    themes.sort(key=lambda t: (severity_order.get(t["severity"], 4), -t["count"]))

    # ------------------------------------------------------------------
    # Channel breakdown
    # ------------------------------------------------------------------
    channels = set(f["source"] for f in all_feedback)
    channel_breakdown: dict[str, dict] = {}
    for channel in channels:
        channel_entries = [f for f in all_feedback if f["source"] == channel]
        pos = sum(1 for e in channel_entries if e["sentiment"] == "positive")
        neg = sum(1 for e in channel_entries if e["sentiment"] == "negative")
        n = len(channel_entries)
        channel_breakdown[channel] = {
            "total": n,
            "positive": pos,
            "negative": neg,
            "neutral": n - pos - neg,
            "negative_pct": round(neg / n * 100, 1) if n > 0 else 0.0,
            "score": round((pos - neg) / n, 3) if n > 0 else 0.0,
        }

    # ------------------------------------------------------------------
    # Tier breakdown
    # ------------------------------------------------------------------
    tiers = set(f["user_tier"] for f in all_feedback)
    tier_breakdown: dict[str, dict] = {}
    for tier in tiers:
        tier_entries = [f for f in all_feedback if f["user_tier"] == tier]
        pos = sum(1 for e in tier_entries if e["sentiment"] == "positive")
        neg = sum(1 for e in tier_entries if e["sentiment"] == "negative")
        n = len(tier_entries)
        tier_breakdown[tier] = {
            "total": n,
            "positive": pos,
            "negative": neg,
            "neutral": n - pos - neg,
            "negative_pct": round(neg / n * 100, 1) if n > 0 else 0.0,
            "score": round((pos - neg) / n, 3) if n > 0 else 0.0,
        }

    enterprise_negative_pct = tier_breakdown.get("enterprise", {}).get("negative_pct", 0.0)

    # ------------------------------------------------------------------
    # Critical signals
    # ------------------------------------------------------------------
    theme_counts = {t["theme"]: t["count"] for t in themes}
    critical_signals: list[str] = []

    if _theme_count_by_label(themes, "App crashes & freezes") >= 4:
        critical_signals.append("crash_epidemic")
    if _theme_count_by_label(themes, "Payment failures & billing errors") >= 2:
        critical_signals.append("payment_failure_spike")
    if _theme_count_by_label(themes, "Cancellation & churn signals") >= 2:
        critical_signals.append("churn_risk_elevated")
    if _theme_count_by_label(themes, "Data loss, sync, & migration issues") >= 2:
        critical_signals.append("data_integrity_risk")
    if enterprise_negative_pct >= 40:
        critical_signals.append("enterprise_accounts_at_risk")
    if score < -0.3:
        critical_signals.append("majority_negative_sentiment")

    # ------------------------------------------------------------------
    # Verbatim highlights
    # ------------------------------------------------------------------
    verbatim_highlights: dict[str, list[str]] = {
        "most_negative": [],
        "most_positive": [],
    }
    if include_quotes:
        neg_entries = [f for f in all_feedback if f["sentiment"] == "negative"]
        pos_entries = [f for f in all_feedback if f["sentiment"] == "positive"]
        # Prioritise enterprise and pro for most_negative (higher business impact)
        neg_sorted = sorted(
            neg_entries,
            key=lambda e: (0 if e["user_tier"] == "enterprise" else 1 if e["user_tier"] == "pro" else 2)
        )
        verbatim_highlights["most_negative"] = [
            e["text"][:150] + ("..." if len(e["text"]) > 150 else "")
            for e in neg_sorted[:3]
        ]
        verbatim_highlights["most_positive"] = [
            e["text"][:150] + ("..." if len(e["text"]) > 150 else "")
            for e in pos_entries[:3]
        ]

    return SentimentReport(
        overall_score=score,
        total_entries=total,
        distribution=dist,
        distribution_pct={
            k: round(v / total * 100, 1) for k, v in dist.items()
        },
        dominant_sentiment=dominant,
        critical_signals=critical_signals,
        themes=themes,
        channel_breakdown=channel_breakdown,
        tier_breakdown=tier_breakdown,
        enterprise_negative_pct=enterprise_negative_pct,
        verbatim_highlights=verbatim_highlights,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _theme_count(themes: list[ThemeSummary], theme_key: str) -> int:
    """Count entries for a theme by its THEME_DEFINITIONS key."""
    label = THEME_DEFINITIONS.get(theme_key, {}).get("label", "")
    return _theme_count_by_label(themes, label)


def _theme_count_by_label(themes: list[ThemeSummary], label: str) -> int:
    for t in themes:
        if t["theme"] == label:
            return t["count"]
    return 0


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("KairosAI — sentiment_analyzer tool")
    print("=" * 60)

    report = sentiment_analyzer()

    print(f"\nOverall sentiment score: {report['overall_score']:+.3f}  (range: -1.0 to +1.0)")
    print(f"Dominant sentiment: {report['dominant_sentiment'].upper()}")
    print(f"Distribution: {report['distribution_pct']}")
    print(f"Enterprise negative %: {report['enterprise_negative_pct']}%")
    print(f"\nCritical signals: {report['critical_signals']}")

    print("\nTop themes:")
    for t in report["themes"]:
        print(f"  [{t['severity'].upper():8}] {t['theme']} — {t['count']} mentions")
        for q in t["representative_quotes"][:1]:
            print(f"           └─ \"{q[:80]}...\"")

    print("\nChannel breakdown:")
    for ch, data in sorted(report["channel_breakdown"].items()):
        print(f"  {ch:<20} neg: {data['negative_pct']}%  score: {data['score']:+.3f}")

    print("\nTier breakdown:")
    for tier, data in sorted(report["tier_breakdown"].items()):
        print(f"  {tier:<12} neg: {data['negative_pct']}%  score: {data['score']:+.3f}")