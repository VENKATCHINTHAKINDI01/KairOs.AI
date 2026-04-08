"""
KairosAI — Mock Metrics Dataset
--------------------------------
10-day time series for 8 KPIs covering the PurpleMerit feature launch window.
Days 1-3: pre-launch baseline
Days 4-10: post-launch, with degradation signals appearing from Day 6 onwards.

All values are realistic for a mid-size SaaS product (~50k DAU).
"""

from datetime import date, timedelta
from typing import TypedDict

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class DailyMetrics(TypedDict):
    date: str
    activation_rate: float          # % of new sign-ups who complete activation
    dau: int                        # Daily Active Users
    wau: int                        # Weekly Active Users (rolling 7-day)
    retention_d1: float             # % of Day-0 users returning on Day 1
    retention_d7: float             # % of Day-0 users returning on Day 7
    crash_rate: float               # crashes per 1000 sessions
    error_rate: float               # API 5xx error rate (%)
    p95_latency_ms: int             # p95 API response time in milliseconds
    payment_success_rate: float     # % of payment attempts that succeed
    support_tickets: int            # new support tickets opened that day
    feature_adoption_funnel: float  # % of eligible users who complete the new feature flow
    daily_churn: int                # accounts that cancelled that day


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

_LAUNCH_DATE = date(2025, 7, 7)   # Day 4 in our dataset

def _d(offset: int) -> str:
    return (_LAUNCH_DATE - timedelta(days=3) + timedelta(days=offset)).isoformat()


RAW_METRICS: list[DailyMetrics] = [
    # ------------------------------------------------------------------
    # PRE-LAUNCH BASELINE  (Days 1-3 — stable, healthy numbers)
    # ------------------------------------------------------------------
    {
        "date": _d(0),
        "activation_rate": 68.2,
        "dau": 48_340,
        "wau": 182_100,
        "retention_d1": 61.5,
        "retention_d7": 38.4,
        "crash_rate": 0.8,
        "error_rate": 0.12,
        "p95_latency_ms": 210,
        "payment_success_rate": 98.7,
        "support_tickets": 34,
        "feature_adoption_funnel": 0.0,   # feature not yet live
        "daily_churn": 12,
    },
    {
        "date": _d(1),
        "activation_rate": 67.8,
        "dau": 47_910,
        "wau": 181_400,
        "retention_d1": 62.1,
        "retention_d7": 38.1,
        "crash_rate": 0.9,
        "error_rate": 0.11,
        "p95_latency_ms": 215,
        "payment_success_rate": 98.9,
        "support_tickets": 31,
        "feature_adoption_funnel": 0.0,
        "daily_churn": 10,
    },
    {
        "date": _d(2),
        "activation_rate": 68.5,
        "dau": 48_620,
        "wau": 182_900,
        "retention_d1": 61.8,
        "retention_d7": 38.6,
        "crash_rate": 0.7,
        "error_rate": 0.10,
        "p95_latency_ms": 208,
        "payment_success_rate": 99.1,
        "support_tickets": 28,
        "feature_adoption_funnel": 0.0,
        "daily_churn": 9,
    },

    # ------------------------------------------------------------------
    # LAUNCH DAY (Day 4 — excitement spike, minor jitter)
    # ------------------------------------------------------------------
    {
        "date": _d(3),
        "activation_rate": 74.1,       # +8.5% spike — marketing push
        "dau": 53_200,
        "wau": 185_800,
        "retention_d1": 63.5,
        "retention_d7": 38.8,
        "crash_rate": 1.4,             # minor uptick from new code path
        "error_rate": 0.18,
        "p95_latency_ms": 248,         # slightly elevated under load
        "payment_success_rate": 98.5,
        "support_tickets": 62,         # doubled — curiosity / onboarding questions
        "feature_adoption_funnel": 22.3,
        "daily_churn": 11,
    },

    # ------------------------------------------------------------------
    # DAYS 5-6 — early signals look OK, then cracks appear
    # ------------------------------------------------------------------
    {
        "date": _d(4),
        "activation_rate": 71.6,
        "dau": 51_800,
        "wau": 186_400,
        "retention_d1": 60.9,
        "retention_d7": 37.5,
        "crash_rate": 1.6,
        "error_rate": 0.22,
        "p95_latency_ms": 264,
        "payment_success_rate": 98.1,
        "support_tickets": 78,
        "feature_adoption_funnel": 31.5,
        "daily_churn": 14,
    },
    {
        "date": _d(5),
        "activation_rate": 69.3,
        "dau": 50_440,
        "wau": 186_100,
        "retention_d1": 59.8,         # D1 retention starting to slide
        "retention_d7": 36.9,
        "crash_rate": 2.1,            # ⚠️ creeping up
        "error_rate": 0.31,
        "p95_latency_ms": 295,
        "payment_success_rate": 97.6,
        "support_tickets": 94,
        "feature_adoption_funnel": 35.2,
        "daily_churn": 17,
    },

    # ------------------------------------------------------------------
    # DAYS 7-8 — RED ZONE — multiple KPIs breach thresholds
    # ------------------------------------------------------------------
    {
        "date": _d(6),
        "activation_rate": 63.8,      # ↓ below baseline — friction in new flow
        "dau": 47_100,                # ↓ dropping below pre-launch
        "wau": 184_300,
        "retention_d1": 55.2,         # 🚨 -10pp from launch day
        "retention_d7": 35.1,
        "crash_rate": 2.9,            # 🚨 3.6× pre-launch baseline
        "error_rate": 0.54,           # 🚨 5× baseline
        "p95_latency_ms": 381,        # 🚨 82% above baseline
        "payment_success_rate": 96.2, # ⚠️ payment failures emerging
        "support_tickets": 148,       # 🚨 4.3× baseline
        "feature_adoption_funnel": 28.4,  # ↓ users abandoning the flow
        "daily_churn": 31,            # ⚠️ 2.6× baseline
    },
    {
        "date": _d(7),
        "activation_rate": 61.2,
        "dau": 45_600,
        "wau": 182_700,
        "retention_d1": 53.8,
        "retention_d7": 34.2,
        "crash_rate": 3.1,
        "error_rate": 0.61,
        "p95_latency_ms": 412,
        "payment_success_rate": 95.8,  # 🚨 lost 3.3pp in 4 days
        "support_tickets": 163,
        "feature_adoption_funnel": 24.1,
        "daily_churn": 38,
    },

    # ------------------------------------------------------------------
    # DAYS 9-10 — hot-patch partially applied, mixed recovery
    # ------------------------------------------------------------------
    {
        "date": _d(8),
        "activation_rate": 63.5,
        "dau": 46_200,
        "wau": 182_100,
        "retention_d1": 55.1,
        "retention_d7": 34.6,
        "crash_rate": 2.6,            # ↓ patch helped crash rate
        "error_rate": 0.48,
        "p95_latency_ms": 368,
        "payment_success_rate": 96.4,
        "support_tickets": 141,
        "feature_adoption_funnel": 26.8,
        "daily_churn": 33,
    },
    {
        "date": _d(9),
        "activation_rate": 64.1,
        "dau": 46_800,
        "wau": 182_500,
        "retention_d1": 56.0,
        "retention_d7": 35.0,
        "crash_rate": 2.4,
        "error_rate": 0.43,
        "p95_latency_ms": 352,
        "payment_success_rate": 96.7,
        "support_tickets": 128,
        "feature_adoption_funnel": 28.0,
        "daily_churn": 29,
    },
]


# ---------------------------------------------------------------------------
# Derived helpers
# ---------------------------------------------------------------------------

def get_baseline() -> list[DailyMetrics]:
    """Return the 3-day pre-launch baseline."""
    return RAW_METRICS[:3]


def get_post_launch() -> list[DailyMetrics]:
    """Return only post-launch days (Day 4 onwards)."""
    return RAW_METRICS[3:]


def get_all() -> list[DailyMetrics]:
    """Return the full 10-day dataset."""
    return RAW_METRICS


def get_latest() -> DailyMetrics:
    """Return the most recent day's metrics."""
    return RAW_METRICS[-1]


def get_by_date(target: str) -> DailyMetrics | None:
    """Look up metrics for a specific date (ISO format YYYY-MM-DD)."""
    return next((m for m in RAW_METRICS if m["date"] == target), None)


# ---------------------------------------------------------------------------
# KPI metadata (for tools to reference thresholds)
# ---------------------------------------------------------------------------

KPI_THRESHOLDS = {
    "activation_rate":          {"warn": 65.0,  "critical": 60.0,  "direction": "higher_better"},
    "dau":                      {"warn": 46000,  "critical": 44000, "direction": "higher_better"},
    "retention_d1":             {"warn": 58.0,   "critical": 55.0,  "direction": "higher_better"},
    "retention_d7":             {"warn": 36.0,   "critical": 34.0,  "direction": "higher_better"},
    "crash_rate":               {"warn": 1.5,    "critical": 2.5,   "direction": "lower_better"},
    "error_rate":               {"warn": 0.25,   "critical": 0.50,  "direction": "lower_better"},
    "p95_latency_ms":           {"warn": 300,    "critical": 400,   "direction": "lower_better"},
    "payment_success_rate":     {"warn": 97.5,   "critical": 96.5,  "direction": "higher_better"},
    "support_tickets":          {"warn": 80,     "critical": 120,   "direction": "lower_better"},
    "feature_adoption_funnel":  {"warn": 30.0,   "critical": 20.0,  "direction": "higher_better"},
    "daily_churn":              {"warn": 20,     "critical": 35,    "direction": "lower_better"},
}


if __name__ == "__main__":
    import json
    print(f"Total days: {len(RAW_METRICS)}")
    print(f"Date range: {RAW_METRICS[0]['date']} → {RAW_METRICS[-1]['date']}")
    print("\nLatest snapshot:")
    print(json.dumps(get_latest(), indent=2))