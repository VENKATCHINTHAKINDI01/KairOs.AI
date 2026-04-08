"""
KairosAI — Mock User Feedback Dataset
---------------------------------------
35 short feedback entries collected via in-app survey, app store reviews,
support tickets, and social listening during the PurpleMerit feature launch.

Mix: ~30% positive, ~20% neutral, ~50% negative (reflecting the degrading launch).
Includes repeated issue themes, a few outliers, and varying sentiment intensity.
"""

from typing import TypedDict


class FeedbackEntry(TypedDict):
    id: int
    source: str         # "in_app" | "app_store" | "support_ticket" | "twitter" | "email"
    date: str           # ISO date
    sentiment: str      # "positive" | "neutral" | "negative"
    text: str
    user_tier: str      # "free" | "pro" | "enterprise"
    feature_tag: str    # primary feature being discussed


RAW_FEEDBACK: list[FeedbackEntry] = [
    # ------------------------------------------------------------------
    # POSITIVE — genuine appreciation, early adopters excited
    # ------------------------------------------------------------------
    {
        "id": 1,
        "source": "in_app",
        "date": "2025-07-07",
        "sentiment": "positive",
        "text": "The new smart dashboard is exactly what I've been asking for. Loved the onboarding tooltips!",
        "user_tier": "pro",
        "feature_tag": "smart_dashboard",
    },
    {
        "id": 2,
        "source": "app_store",
        "date": "2025-07-07",
        "sentiment": "positive",
        "text": "5 stars. The AI summary feature saves me 30 mins every morning. Keep shipping stuff like this.",
        "user_tier": "pro",
        "feature_tag": "ai_summary",
    },
    {
        "id": 3,
        "source": "twitter",
        "date": "2025-07-08",
        "sentiment": "positive",
        "text": "@PurpleMerit just dropped a banger update. The new analytics view is 🔥",
        "user_tier": "free",
        "feature_tag": "analytics_view",
    },
    {
        "id": 4,
        "source": "in_app",
        "date": "2025-07-08",
        "sentiment": "positive",
        "text": "Really clean UX on the new feature. Our team adopted it within hours.",
        "user_tier": "enterprise",
        "feature_tag": "smart_dashboard",
    },
    {
        "id": 5,
        "source": "email",
        "date": "2025-07-09",
        "sentiment": "positive",
        "text": "Love the new collaborative notes. Finally our whole team is on the same page.",
        "user_tier": "pro",
        "feature_tag": "collaborative_notes",
    },
    {
        "id": 6,
        "source": "in_app",
        "date": "2025-07-10",
        "sentiment": "positive",
        "text": "App is snappier than before — nice perf improvement alongside the new feature.",
        "user_tier": "free",
        "feature_tag": "performance",
    },
    {
        "id": 7,
        "source": "app_store",
        "date": "2025-07-11",
        "sentiment": "positive",
        "text": "Best product update in 2 years. Worth every penny of my Pro subscription.",
        "user_tier": "pro",
        "feature_tag": "smart_dashboard",
    },
    {
        "id": 8,
        "source": "email",
        "date": "2025-07-14",
        "sentiment": "positive",
        "text": "Noticed things have gotten better after yesterday's patch — good recovery, team!",
        "user_tier": "enterprise",
        "feature_tag": "performance",
    },
    {
        "id": 9,
        "source": "in_app",
        "date": "2025-07-14",
        "sentiment": "positive",
        "text": "Finally got the feature to work after clearing cache. It's actually really useful.",
        "user_tier": "pro",
        "feature_tag": "smart_dashboard",
    },

    # ------------------------------------------------------------------
    # NEUTRAL — mixed feelings, uncertainty, wait-and-see
    # ------------------------------------------------------------------
    {
        "id": 10,
        "source": "in_app",
        "date": "2025-07-08",
        "sentiment": "neutral",
        "text": "Not sure if the new layout is better or worse. Need more time with it.",
        "user_tier": "free",
        "feature_tag": "smart_dashboard",
    },
    {
        "id": 11,
        "source": "support_ticket",
        "date": "2025-07-09",
        "sentiment": "neutral",
        "text": "The new feature works for me but my colleague can't access it. Is it a permissions issue?",
        "user_tier": "pro",
        "feature_tag": "access_control",
    },
    {
        "id": 12,
        "source": "twitter",
        "date": "2025-07-10",
        "sentiment": "neutral",
        "text": "Tried the new PurpleMerit feature — interesting but not sure it fits my workflow yet.",
        "user_tier": "free",
        "feature_tag": "smart_dashboard",
    },
    {
        "id": 13,
        "source": "in_app",
        "date": "2025-07-11",
        "sentiment": "neutral",
        "text": "Some things are slower, some things are faster. Net-neutral for me right now.",
        "user_tier": "pro",
        "feature_tag": "performance",
    },
    {
        "id": 14,
        "source": "email",
        "date": "2025-07-12",
        "sentiment": "neutral",
        "text": "Had a few hiccups but support resolved them. Keeping an eye on stability this week.",
        "user_tier": "enterprise",
        "feature_tag": "stability",
    },
    {
        "id": 15,
        "source": "in_app",
        "date": "2025-07-13",
        "sentiment": "neutral",
        "text": "The mobile app is fine. Desktop still feels off. Hoping the next patch fixes it.",
        "user_tier": "pro",
        "feature_tag": "cross_platform",
    },

    # ------------------------------------------------------------------
    # NEGATIVE — frustration, crashes, performance, data issues
    # ------------------------------------------------------------------

    # CRASH / APP FREEZE — repeated theme
    {
        "id": 16,
        "source": "support_ticket",
        "date": "2025-07-10",
        "sentiment": "negative",
        "text": "App keeps crashing when I open the smart dashboard. Submitted 3 tickets. No fix yet.",
        "user_tier": "pro",
        "feature_tag": "crash",
    },
    {
        "id": 17,
        "source": "app_store",
        "date": "2025-07-11",
        "sentiment": "negative",
        "text": "1 star. App crashes every time I try the new feature. Unusable. Downgrading to previous version.",
        "user_tier": "free",
        "feature_tag": "crash",
    },
    {
        "id": 18,
        "source": "twitter",
        "date": "2025-07-11",
        "sentiment": "negative",
        "text": "@PurpleMerit your app is CRASHING every 10 minutes since the update. Fix this ASAP!",
        "user_tier": "pro",
        "feature_tag": "crash",
    },
    {
        "id": 19,
        "source": "support_ticket",
        "date": "2025-07-12",
        "sentiment": "negative",
        "text": "The dashboard freezes for 30+ seconds then crashes. Reproducible every time on iOS 17.",
        "user_tier": "enterprise",
        "feature_tag": "crash",
    },
    {
        "id": 20,
        "source": "in_app",
        "date": "2025-07-12",
        "sentiment": "negative",
        "text": "Can't use the app at all since the update. Crashes on startup half the time.",
        "user_tier": "free",
        "feature_tag": "crash",
    },

    # PERFORMANCE / LATENCY — repeated theme
    {
        "id": 21,
        "source": "in_app",
        "date": "2025-07-10",
        "sentiment": "negative",
        "text": "Everything is so slow now. Loading screens everywhere. What happened to the speed?",
        "user_tier": "free",
        "feature_tag": "performance",
    },
    {
        "id": 22,
        "source": "support_ticket",
        "date": "2025-07-11",
        "sentiment": "negative",
        "text": "API response times have jumped since the update. Our integrations are timing out.",
        "user_tier": "enterprise",
        "feature_tag": "performance",
    },
    {
        "id": 23,
        "source": "twitter",
        "date": "2025-07-12",
        "sentiment": "negative",
        "text": "PurpleMerit used to be the fastest tool in its category. Not anymore after this update.",
        "user_tier": "pro",
        "feature_tag": "performance",
    },
    {
        "id": 24,
        "source": "email",
        "date": "2025-07-12",
        "sentiment": "negative",
        "text": "Our team is experiencing 20-30s load times on the new dashboard. Pre-update it was 2s.",
        "user_tier": "enterprise",
        "feature_tag": "performance",
    },

    # PAYMENT / BILLING ISSUE — high severity
    {
        "id": 25,
        "source": "support_ticket",
        "date": "2025-07-11",
        "sentiment": "negative",
        "text": "My payment failed twice trying to upgrade to Pro. Card is valid. This is embarrassing.",
        "user_tier": "free",
        "feature_tag": "payment",
    },
    {
        "id": 26,
        "source": "email",
        "date": "2025-07-12",
        "sentiment": "negative",
        "text": "Got a payment failure notification but I was charged anyway. Need a refund immediately.",
        "user_tier": "pro",
        "feature_tag": "payment",
    },
    {
        "id": 27,
        "source": "support_ticket",
        "date": "2025-07-13",
        "sentiment": "negative",
        "text": "Tried to renew our enterprise license and the payment page errors out. This is blocking our team.",
        "user_tier": "enterprise",
        "feature_tag": "payment",
    },

    # DATA / SYNC ISSUES
    {
        "id": 28,
        "source": "support_ticket",
        "date": "2025-07-11",
        "sentiment": "negative",
        "text": "My data didn't migrate correctly to the new dashboard. Missing 2 weeks of history.",
        "user_tier": "pro",
        "feature_tag": "data_migration",
    },
    {
        "id": 29,
        "source": "in_app",
        "date": "2025-07-12",
        "sentiment": "negative",
        "text": "Reports are showing wrong numbers since the update. My old data looks corrupted.",
        "user_tier": "enterprise",
        "feature_tag": "data_integrity",
    },
    {
        "id": 30,
        "source": "email",
        "date": "2025-07-13",
        "sentiment": "negative",
        "text": "Syncing between web and mobile is completely broken. Data is inconsistent across both.",
        "user_tier": "pro",
        "feature_tag": "data_sync",
    },

    # CANCELLATION / CHURN SIGNALS — outlier severity
    {
        "id": 31,
        "source": "email",
        "date": "2025-07-13",
        "sentiment": "negative",
        "text": "We're pausing our enterprise contract until stability is restored. Please contact our account manager.",
        "user_tier": "enterprise",
        "feature_tag": "churn_signal",
    },
    {
        "id": 32,
        "source": "support_ticket",
        "date": "2025-07-13",
        "sentiment": "negative",
        "text": "Cancelled my Pro subscription today. The crashes are too frequent for a paid product.",
        "user_tier": "pro",
        "feature_tag": "churn_signal",
    },
    {
        "id": 33,
        "source": "twitter",
        "date": "2025-07-14",
        "sentiment": "negative",
        "text": "Been a PurpleMerit customer for 3 years. The latest update has made me seriously consider switching.",
        "user_tier": "pro",
        "feature_tag": "churn_signal",
    },

    # OUTLIER — Unusually technical complaint (power user)
    {
        "id": 34,
        "source": "email",
        "date": "2025-07-12",
        "sentiment": "negative",
        "text": (
            "Your new feature is making 3x more API calls per render cycle than the old one. "
            "I measured it with Charles Proxy. This explains the latency spike. Classic N+1 pattern. "
            "Happy to share the HAR file if your engineers need it."
        ),
        "user_tier": "enterprise",
        "feature_tag": "performance",
    },

    # OUTLIER — Positive but edge case (accessibility)
    {
        "id": 35,
        "source": "email",
        "date": "2025-07-09",
        "sentiment": "positive",
        "text": (
            "The new high-contrast mode in the dashboard is a game-changer for me as a visually impaired user. "
            "Thank you for caring about accessibility. More products should do this."
        ),
        "user_tier": "free",
        "feature_tag": "accessibility",
    },
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_all() -> list[FeedbackEntry]:
    return RAW_FEEDBACK


def get_by_sentiment(sentiment: str) -> list[FeedbackEntry]:
    """Filter feedback by sentiment: 'positive', 'neutral', or 'negative'."""
    return [f for f in RAW_FEEDBACK if f["sentiment"] == sentiment]


def get_by_source(source: str) -> list[FeedbackEntry]:
    """Filter by source channel."""
    return [f for f in RAW_FEEDBACK if f["source"] == source]


def get_by_feature(tag: str) -> list[FeedbackEntry]:
    """Filter by feature tag."""
    return [f for f in RAW_FEEDBACK if f["feature_tag"] == tag]


def get_by_tier(tier: str) -> list[FeedbackEntry]:
    """Filter by user tier: 'free', 'pro', or 'enterprise'."""
    return [f for f in RAW_FEEDBACK if f["user_tier"] == tier]


def get_summary_stats() -> dict:
    """Return high-level counts for quick reference."""
    total = len(RAW_FEEDBACK)
    by_sentiment = {
        "positive": len(get_by_sentiment("positive")),
        "neutral": len(get_by_sentiment("neutral")),
        "negative": len(get_by_sentiment("negative")),
    }
    by_source = {}
    for entry in RAW_FEEDBACK:
        by_source[entry["source"]] = by_source.get(entry["source"], 0) + 1

    return {
        "total": total,
        "by_sentiment": by_sentiment,
        "by_source": by_source,
        "negative_pct": round(by_sentiment["negative"] / total * 100, 1),
        "positive_pct": round(by_sentiment["positive"] / total * 100, 1),
    }


if __name__ == "__main__":
    import json
    stats = get_summary_stats()
    print("Feedback summary:")
    print(json.dumps(stats, indent=2))
    print(f"\nChurn signals: {len(get_by_feature('churn_signal'))}")
    print(f"Crash mentions: {len(get_by_feature('crash'))}")
    print(f"Payment issues: {len(get_by_feature('payment'))}")
    print(f"Enterprise feedback: {len(get_by_tier('enterprise'))}")