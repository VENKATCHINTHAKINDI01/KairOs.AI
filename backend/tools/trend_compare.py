"""
KairosAI — Tool: trend_compare
--------------------------------
Compares pre-launch baseline vs post-launch performance for each KPI.
Produces:
  - Percentage change from baseline to peak degradation
  - Percentage change from baseline to current (latest day)
  - Recovery progress (if any)
  - Weighted impact score per KPI
  - Overall launch impact verdict

Called by: Data Analyst Agent, PM Agent
"""

from typing import TypedDict
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.metrics import get_baseline, get_post_launch, get_latest, KPI_THRESHOLDS


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------

class KPIComparison(TypedDict):
    kpi: str
    direction: str                  # "higher_better" | "lower_better"
    baseline_avg: float
    peak_degraded_value: float      # worst post-launch value
    peak_degraded_date: str
    current_value: float
    baseline_to_peak_pct: float     # % change from baseline to worst point
    baseline_to_current_pct: float  # % change from baseline to now
    recovery_pct: float             # how much of the degradation has been recovered (0-100%)
    impact_score: float             # 0-10, weighted by threshold proximity
    verdict: str                    # "stable" | "degraded" | "recovering" | "recovered"


class TrendReport(TypedDict):
    launch_impact_verdict: str          # "minimal" | "moderate" | "severe" | "catastrophic"
    avg_impact_score: float             # 0-10
    worst_kpi: str
    most_recovered_kpi: str | None
    kpis_still_degraded: list[str]
    kpis_recovering: list[str]
    days_since_launch: int
    key_findings: list[str]             # 3-5 bullet-point findings for agents
    comparisons: list[KPIComparison]


# ---------------------------------------------------------------------------
# KPI weights — how important is each KPI to the launch decision?
# Scale: 1.0 (low) to 3.0 (critical business impact)
# ---------------------------------------------------------------------------

KPI_WEIGHTS = {
    "crash_rate": 3.0,
    "payment_success_rate": 3.0,
    "retention_d1": 2.5,
    "retention_d7": 2.5,
    "error_rate": 2.0,
    "p95_latency_ms": 2.0,
    "support_tickets": 1.5,
    "daily_churn": 2.0,
    "activation_rate": 1.5,
    "dau": 1.5,
    "wau": 1.0,
    "feature_adoption_funnel": 1.0,
}


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def trend_compare(kpis: list[str] | None = None) -> TrendReport:
    """
    Compare baseline vs post-launch KPI trends.

    Args:
        kpis: KPI keys to compare. Defaults to all.

    Returns:
        TrendReport with per-KPI comparisons and overall launch impact.
    """
    if kpis is None:
        kpis = list(KPI_THRESHOLDS.keys())

    baseline_days = get_baseline()
    post_launch_days = get_post_launch()
    latest = get_latest()

    comparisons: list[KPIComparison] = []

    for kpi in kpis:
        if kpi not in KPI_THRESHOLDS:
            continue

        direction = KPI_THRESHOLDS[kpi]["direction"]

        # Baseline average
        baseline_vals = [float(d[kpi]) for d in baseline_days if kpi in d]
        if not baseline_vals:
            continue
        baseline_avg = sum(baseline_vals) / len(baseline_vals)

        # Find peak degradation in post-launch window
        post_vals = [(d["date"], float(d[kpi])) for d in post_launch_days if kpi in d]
        if not post_vals:
            continue

        if direction == "lower_better":
            # Worst = highest value
            peak_date, peak_val = max(post_vals, key=lambda x: x[1])
        else:
            # Worst = lowest value
            peak_date, peak_val = min(post_vals, key=lambda x: x[1])

        current_value = float(latest.get(kpi, 0))

        # % changes (signed, from baseline perspective)
        baseline_to_peak_pct = _pct_change(baseline_avg, peak_val, direction)
        baseline_to_current_pct = _pct_change(baseline_avg, current_value, direction)

        # Recovery progress
        # 0% = still at peak degradation, 100% = fully back to baseline
        total_degradation = abs(baseline_to_peak_pct)
        current_degradation = abs(baseline_to_current_pct)
        if total_degradation > 0:
            recovery_pct = max(0.0, round((1 - current_degradation / total_degradation) * 100, 1))
        else:
            recovery_pct = 100.0

        # Impact score (0-10)
        # Uses peak degradation magnitude, weighted by KPI importance
        weight = KPI_WEIGHTS.get(kpi, 1.0)
        raw_impact = min(total_degradation / 30.0, 1.0)  # 30% degradation = max raw score
        impact_score = round(raw_impact * weight * (10.0 / 3.0), 2)  # scale to 0-10
        impact_score = min(impact_score, 10.0)

        # Verdict
        if total_degradation < 3.0:
            verdict = "stable"
        elif recovery_pct >= 80:
            verdict = "recovered"
        elif recovery_pct >= 30:
            verdict = "recovering"
        else:
            verdict = "degraded"

        comparisons.append(KPIComparison(
            kpi=kpi,
            direction=direction,
            baseline_avg=round(baseline_avg, 2),
            peak_degraded_value=round(peak_val, 2),
            peak_degraded_date=peak_date,
            current_value=round(current_value, 2),
            baseline_to_peak_pct=round(baseline_to_peak_pct, 1),
            baseline_to_current_pct=round(baseline_to_current_pct, 1),
            recovery_pct=recovery_pct,
            impact_score=impact_score,
            verdict=verdict,
        ))

    # ------------------------------------------------------------------
    # Roll-up
    # ------------------------------------------------------------------
    if not comparisons:
        return TrendReport(
            launch_impact_verdict="unknown",
            avg_impact_score=0.0,
            worst_kpi="",
            most_recovered_kpi=None,
            kpis_still_degraded=[],
            kpis_recovering=[],
            days_since_launch=len(post_launch_days),
            key_findings=["Insufficient data for trend analysis."],
            comparisons=[],
        )

    avg_impact = round(sum(c["impact_score"] for c in comparisons) / len(comparisons), 2)
    worst = max(comparisons, key=lambda c: c["impact_score"])
    recovering = [c for c in comparisons if c["verdict"] == "recovering"]
    degraded = [c for c in comparisons if c["verdict"] == "degraded"]

    most_recovered = (
        max(recovering, key=lambda c: c["recovery_pct"])
        if recovering else None
    )

    # Launch impact verdict
    if avg_impact >= 6.0:
        launch_verdict = "catastrophic"
    elif avg_impact >= 3.5:
        launch_verdict = "severe"
    elif avg_impact >= 1.5:
        launch_verdict = "moderate"
    else:
        launch_verdict = "minimal"

    # Key findings (narrative bullets)
    key_findings = _generate_findings(comparisons, worst, avg_impact, launch_verdict)

    return TrendReport(
        launch_impact_verdict=launch_verdict,
        avg_impact_score=avg_impact,
        worst_kpi=worst["kpi"],
        most_recovered_kpi=most_recovered["kpi"] if most_recovered else None,
        kpis_still_degraded=[c["kpi"] for c in degraded],
        kpis_recovering=[c["kpi"] for c in recovering],
        days_since_launch=len(post_launch_days),
        key_findings=key_findings,
        comparisons=sorted(comparisons, key=lambda c: -c["impact_score"]),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct_change(baseline: float, current: float, direction: str) -> float:
    """
    Returns % change expressed as a negative number when degrading.
    For lower_better: positive change = degradation → return negative.
    For higher_better: negative change = degradation → return as-is (negative).
    """
    if baseline == 0:
        return 0.0
    raw = ((current - baseline) / baseline) * 100
    if direction == "lower_better":
        return -raw   # flip so degradation is always negative
    return raw


def _generate_findings(
    comparisons: list[KPIComparison],
    worst: KPIComparison,
    avg_impact: float,
    verdict: str,
) -> list[str]:
    """Generate 4-6 key finding bullets for agent consumption."""
    findings = []

    findings.append(
        f"Launch impact is {verdict.upper()}: average KPI impact score {avg_impact}/10 "
        f"across {len(comparisons)} KPIs."
    )
    findings.append(
        f"Worst affected KPI: {worst['kpi']} — degraded {abs(worst['baseline_to_peak_pct']):.1f}% "
        f"from baseline (impact score: {worst['impact_score']:.1f}/10)."
    )

    degraded = [c for c in comparisons if c["verdict"] == "degraded"]
    if degraded:
        degraded_names = ", ".join(c["kpi"] for c in degraded[:4])
        findings.append(f"{len(degraded)} KPIs still degraded with no meaningful recovery: {degraded_names}.")

    recovering = [c for c in comparisons if c["verdict"] == "recovering"]
    if recovering:
        best_rec = max(recovering, key=lambda c: c["recovery_pct"])
        findings.append(
            f"{len(recovering)} KPIs showing partial recovery — best is "
            f"{best_rec['kpi']} at {best_rec['recovery_pct']}% recovered."
        )

    stable = [c for c in comparisons if c["verdict"] in ("stable", "recovered")]
    if stable:
        findings.append(f"{len(stable)} KPIs remain stable or fully recovered.")

    # High-value specific insight
    crash_comp = next((c for c in comparisons if c["kpi"] == "crash_rate"), None)
    payment_comp = next((c for c in comparisons if c["kpi"] == "payment_success_rate"), None)

    if crash_comp and crash_comp["verdict"] == "degraded":
        findings.append(
            f"Crash rate is {crash_comp['current_value']}x the critical threshold "
            f"with only {crash_comp['recovery_pct']}% recovery — mobile stability is a blocking issue."
        )
    if payment_comp and payment_comp["baseline_to_current_pct"] < -1.5:
        findings.append(
            f"Payment success rate has dropped {abs(payment_comp['baseline_to_current_pct']):.1f}pp "
            f"from baseline — revenue impact is confirmed."
        )

    return findings[:6]


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("KairosAI — trend_compare tool")
    print("=" * 60)

    report = trend_compare()

    print(f"\nLaunch impact verdict: {report['launch_impact_verdict'].upper()}")
    print(f"Average impact score: {report['avg_impact_score']}/10")
    print(f"Worst KPI: {report['worst_kpi']}")
    print(f"Still degraded: {report['kpis_still_degraded']}")
    print(f"Recovering: {report['kpis_recovering']}")

    print("\nKey findings:")
    for finding in report["key_findings"]:
        print(f"  • {finding}")

    print(f"\n{'KPI':<30} {'Baseline':>10} {'Peak':>10} {'Current':>10} {'Recovery%':>10} {'Impact':>8} {'Verdict':>12}")
    print("-" * 94)
    for c in report["comparisons"]:
        print(
            f"{c['kpi']:<30} "
            f"{c['baseline_avg']:>10.2f} "
            f"{c['peak_degraded_value']:>10.2f} "
            f"{c['current_value']:>10.2f} "
            f"{c['recovery_pct']:>9.1f}% "
            f"{c['impact_score']:>8.2f} "
            f"{c['verdict']:>12}"
        )