"""
KairosAI — Tool: aggregate_metrics
------------------------------------
Computes summary statistics for each KPI:
  - baseline average (pre-launch Days 1-3)
  - current value (latest day)
  - absolute and percentage change
  - status flag: OK | WARN | CRITICAL
  - breach count across the post-launch window

Called by: Data Analyst Agent, PM Agent, SRE Agent
"""

from typing import TypedDict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.metrics import get_baseline, get_post_launch, get_latest, KPI_THRESHOLDS


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------

class KPISummary(TypedDict):
    kpi: str
    baseline_avg: float
    current_value: float
    absolute_change: float
    pct_change: float
    status: str            # "OK" | "WARN" | "CRITICAL"
    direction: str         # "higher_better" | "lower_better"
    breach_days: int       # how many post-launch days breached critical threshold
    trend: str             # "improving" | "stable" | "degrading"


class AggregationResult(TypedDict):
    total_kpis: int
    ok_count: int
    warn_count: int
    critical_count: int
    critical_kpis: list[str]
    overall_health: str     # "healthy" | "degraded" | "critical"
    summaries: list[KPISummary]


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def aggregate_metrics(kpis: list[str] | None = None) -> AggregationResult:
    """
    Aggregate KPI metrics and return a structured summary.

    Args:
        kpis: Optional list of KPI keys to include.
              Defaults to all KPIs in KPI_THRESHOLDS.

    Returns:
        AggregationResult with per-KPI summaries and overall health.
    """
    if kpis is None:
        kpis = list(KPI_THRESHOLDS.keys())

    baseline_days = get_baseline()
    post_launch_days = get_post_launch()
    latest = get_latest()

    summaries: list[KPISummary] = []

    for kpi in kpis:
        if kpi not in KPI_THRESHOLDS:
            continue

        threshold = KPI_THRESHOLDS[kpi]
        direction = threshold["direction"]
        warn_t = threshold["warn"]
        crit_t = threshold["critical"]

        # Baseline average (pre-launch)
        baseline_vals = [day[kpi] for day in baseline_days if kpi in day]
        baseline_avg = round(sum(baseline_vals) / len(baseline_vals), 2) if baseline_vals else 0.0

        # Current value (latest day)
        current_value = float(latest.get(kpi, 0))

        # Change
        absolute_change = round(current_value - baseline_avg, 2)
        pct_change = round((absolute_change / baseline_avg) * 100, 1) if baseline_avg != 0 else 0.0

        # Status — logic differs by direction
        status = _compute_status(current_value, warn_t, crit_t, direction)

        # Breach days — how many post-launch days hit critical
        breach_days = sum(
            1 for day in post_launch_days
            if kpi in day and _compute_status(float(day[kpi]), warn_t, crit_t, direction) == "CRITICAL"
        )

        # Trend — compare last 2 days vs previous 2 days in post-launch window
        trend = _compute_trend(kpi, post_launch_days, direction)

        summaries.append(KPISummary(
            kpi=kpi,
            baseline_avg=baseline_avg,
            current_value=current_value,
            absolute_change=absolute_change,
            pct_change=pct_change,
            status=status,
            direction=direction,
            breach_days=breach_days,
            trend=trend,
        ))

    # Roll up counts
    ok_count = sum(1 for s in summaries if s["status"] == "OK")
    warn_count = sum(1 for s in summaries if s["status"] == "WARN")
    critical_count = sum(1 for s in summaries if s["status"] == "CRITICAL")
    critical_kpis = [s["kpi"] for s in summaries if s["status"] == "CRITICAL"]

    # Overall health
    if critical_count >= 3:
        overall_health = "critical"
    elif critical_count >= 1 or warn_count >= 3:
        overall_health = "degraded"
    else:
        overall_health = "healthy"

    return AggregationResult(
        total_kpis=len(summaries),
        ok_count=ok_count,
        warn_count=warn_count,
        critical_count=critical_count,
        critical_kpis=critical_kpis,
        overall_health=overall_health,
        summaries=summaries,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_status(value: float, warn: float, critical: float, direction: str) -> str:
    """Determine OK / WARN / CRITICAL based on threshold and direction."""
    if direction == "lower_better":
        if value >= critical:
            return "CRITICAL"
        elif value >= warn:
            return "WARN"
        else:
            return "OK"
    else:  # higher_better
        if value <= critical:
            return "CRITICAL"
        elif value <= warn:
            return "WARN"
        else:
            return "OK"


def _compute_trend(kpi: str, post_launch_days: list, direction: str) -> str:
    """
    Compare last 2 days vs previous 2 days.
    Returns: "improving" | "stable" | "degrading"
    """
    if len(post_launch_days) < 4:
        return "stable"

    recent = [float(d[kpi]) for d in post_launch_days[-2:] if kpi in d]
    prior = [float(d[kpi]) for d in post_launch_days[-4:-2] if kpi in d]

    if not recent or not prior:
        return "stable"

    recent_avg = sum(recent) / len(recent)
    prior_avg = sum(prior) / len(prior)
    delta = recent_avg - prior_avg
    pct = abs(delta / prior_avg) * 100 if prior_avg != 0 else 0

    if pct < 2.0:
        return "stable"

    # For lower_better: negative delta = improving (value dropped = good)
    if direction == "lower_better":
        return "improving" if delta < 0 else "degrading"
    else:
        return "improving" if delta > 0 else "degrading"


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("KairosAI — aggregate_metrics tool")
    print("=" * 60)

    result = aggregate_metrics()

    print(f"\nOverall health: {result['overall_health'].upper()}")
    print(f"KPIs: {result['ok_count']} OK  |  {result['warn_count']} WARN  |  {result['critical_count']} CRITICAL")
    print(f"Critical KPIs: {result['critical_kpis']}")

    print("\nDetailed breakdown:")
    print(f"{'KPI':<30} {'Baseline':>10} {'Current':>10} {'Change%':>8} {'Status':>10} {'Trend':>12}")
    print("-" * 82)
    for s in result["summaries"]:
        print(
            f"{s['kpi']:<30} "
            f"{s['baseline_avg']:>10.2f} "
            f"{s['current_value']:>10.2f} "
            f"{s['pct_change']:>+7.1f}% "
            f"{s['status']:>10} "
            f"{s['trend']:>12}"
        )