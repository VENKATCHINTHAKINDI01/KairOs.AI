"""
KairosAI — Tool: detect_anomalies
-----------------------------------
Detects statistical anomalies in the metrics time series using:
  - Z-score (how many standard deviations from the mean)
  - Threshold breach detection
  - Rate-of-change spikes (day-over-day delta)
  - Streak detection (consecutive days in breach)

Called by: Data Analyst Agent, SRE Agent
"""

from typing import TypedDict
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.metrics import get_all, KPI_THRESHOLDS


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------

class Anomaly(TypedDict):
    kpi: str
    date: str
    value: float
    anomaly_type: str       # "zscore_spike" | "threshold_breach" | "rate_spike" | "streak"
    severity: str           # "high" | "medium" | "low"
    zscore: float           # z-score value (for zscore_spike type)
    description: str        # human-readable explanation


class AnomalyReport(TypedDict):
    total_anomalies: int
    high_severity: int
    medium_severity: int
    low_severity: int
    most_anomalous_kpis: list[str]      # KPIs with most anomalies
    anomaly_start_date: str | None      # first date anomalies appeared
    consecutive_breach_kpis: list[str]  # KPIs in breach streak >= 3 days
    anomalies: list[Anomaly]


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def detect_anomalies(
    kpis: list[str] | None = None,
    zscore_threshold: float = 2.0,
    rate_spike_pct: float = 30.0,
    streak_min_days: int = 3,
) -> AnomalyReport:
    """
    Detect anomalies across the metrics time series.

    Args:
        kpis: KPI keys to analyse. Defaults to all.
        zscore_threshold: How many std devs = anomaly (default 2.0).
        rate_spike_pct: Day-over-day % change that counts as a spike (default 30%).
        streak_min_days: Minimum consecutive breach days to flag a streak (default 3).

    Returns:
        AnomalyReport with a full list of detected anomalies.
    """
    if kpis is None:
        kpis = list(KPI_THRESHOLDS.keys())

    all_days = get_all()
    anomalies: list[Anomaly] = []

    for kpi in kpis:
        if kpi not in KPI_THRESHOLDS:
            continue

        threshold = KPI_THRESHOLDS[kpi]
        values = [(day["date"], float(day[kpi])) for day in all_days if kpi in day]

        if len(values) < 3:
            continue

        raw_vals = [v for _, v in values]
        mean = sum(raw_vals) / len(raw_vals)
        std = math.sqrt(sum((x - mean) ** 2 for x in raw_vals) / len(raw_vals))

        # ------------------------------------------------------------------
        # 1. Z-score anomaly detection
        # ------------------------------------------------------------------
        for date, value in values:
            zscore = (value - mean) / std if std > 0 else 0.0
            abs_z = abs(zscore)

            if abs_z >= zscore_threshold:
                severity = "high" if abs_z >= 3.0 else "medium"
                direction_word = (
                    "dangerously high" if (threshold["direction"] == "lower_better" and zscore > 0)
                    else "dangerously low" if (threshold["direction"] == "higher_better" and zscore < 0)
                    else "unusually high" if zscore > 0
                    else "unusually low"
                )
                anomalies.append(Anomaly(
                    kpi=kpi,
                    date=date,
                    value=value,
                    anomaly_type="zscore_spike",
                    severity=severity,
                    zscore=round(zscore, 2),
                    description=(
                        f"{kpi} is {direction_word} on {date} "
                        f"(value: {value}, z-score: {zscore:+.2f}, "
                        f"mean: {mean:.2f}, std: {std:.2f})"
                    ),
                ))

        # ------------------------------------------------------------------
        # 2. Threshold breach detection (critical only)
        # ------------------------------------------------------------------
        crit_t = threshold["critical"]
        for date, value in values:
            is_breach = (
                (threshold["direction"] == "lower_better" and value >= crit_t)
                or (threshold["direction"] == "higher_better" and value <= crit_t)
            )
            # Only add if not already flagged by z-score (avoid duplicates)
            already_flagged = any(
                a["kpi"] == kpi and a["date"] == date and a["anomaly_type"] == "zscore_spike"
                for a in anomalies
            )
            if is_breach and not already_flagged:
                anomalies.append(Anomaly(
                    kpi=kpi,
                    date=date,
                    value=value,
                    anomaly_type="threshold_breach",
                    severity="high",
                    zscore=round((value - mean) / std if std > 0 else 0.0, 2),
                    description=(
                        f"{kpi} breached critical threshold on {date} "
                        f"(value: {value}, critical threshold: {crit_t})"
                    ),
                ))

        # ------------------------------------------------------------------
        # 3. Rate-of-change spike detection
        # ------------------------------------------------------------------
        for i in range(1, len(values)):
            prev_date, prev_val = values[i - 1]
            curr_date, curr_val = values[i]
            if prev_val == 0:
                continue
            rate_change_pct = abs((curr_val - prev_val) / prev_val) * 100

            if rate_change_pct >= rate_spike_pct:
                direction_word = "jumped" if curr_val > prev_val else "dropped"
                severity = "high" if rate_change_pct >= 60 else "medium"
                anomalies.append(Anomaly(
                    kpi=kpi,
                    date=curr_date,
                    value=curr_val,
                    anomaly_type="rate_spike",
                    severity=severity,
                    zscore=round((curr_val - mean) / std if std > 0 else 0.0, 2),
                    description=(
                        f"{kpi} {direction_word} {rate_change_pct:.1f}% "
                        f"from {prev_date} ({prev_val}) to {curr_date} ({curr_val})"
                    ),
                ))

        # ------------------------------------------------------------------
        # 4. Consecutive breach streak detection
        # ------------------------------------------------------------------
        streak = 0
        streak_start = None
        for date, value in values:
            is_breach = (
                (threshold["direction"] == "lower_better" and value >= threshold["warn"])
                or (threshold["direction"] == "higher_better" and value <= threshold["warn"])
            )
            if is_breach:
                streak += 1
                if streak == 1:
                    streak_start = date
            else:
                streak = 0
                streak_start = None

            if streak == streak_min_days:
                anomalies.append(Anomaly(
                    kpi=kpi,
                    date=date,
                    value=value,
                    anomaly_type="streak",
                    severity="high",
                    zscore=round((value - mean) / std if std > 0 else 0.0, 2),
                    description=(
                        f"{kpi} has been in breach for {streak} consecutive days "
                        f"(since {streak_start})"
                    ),
                ))

    # ------------------------------------------------------------------
    # Roll-up statistics
    # ------------------------------------------------------------------
    high_count = sum(1 for a in anomalies if a["severity"] == "high")
    medium_count = sum(1 for a in anomalies if a["severity"] == "medium")
    low_count = sum(1 for a in anomalies if a["severity"] == "low")

    # Most anomalous KPIs
    kpi_counts: dict[str, int] = {}
    for a in anomalies:
        kpi_counts[a["kpi"]] = kpi_counts.get(a["kpi"], 0) + 1
    most_anomalous = sorted(kpi_counts, key=lambda k: kpi_counts[k], reverse=True)[:5]

    # First anomaly date
    all_dates = sorted(set(a["date"] for a in anomalies))
    anomaly_start = all_dates[0] if all_dates else None

    # KPIs in streak breach
    streak_kpis = list(set(a["kpi"] for a in anomalies if a["anomaly_type"] == "streak"))

    return AnomalyReport(
        total_anomalies=len(anomalies),
        high_severity=high_count,
        medium_severity=medium_count,
        low_severity=low_count,
        most_anomalous_kpis=most_anomalous,
        anomaly_start_date=anomaly_start,
        consecutive_breach_kpis=streak_kpis,
        anomalies=anomalies,
    )


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("KairosAI — detect_anomalies tool")
    print("=" * 60)

    report = detect_anomalies()

    print(f"\nTotal anomalies detected: {report['total_anomalies']}")
    print(f"  High severity:   {report['high_severity']}")
    print(f"  Medium severity: {report['medium_severity']}")
    print(f"  Low severity:    {report['low_severity']}")
    print(f"\nMost anomalous KPIs: {report['most_anomalous_kpis']}")
    print(f"Anomalies first appeared: {report['anomaly_start_date']}")
    print(f"KPIs in breach streak: {report['consecutive_breach_kpis']}")

    print("\nHigh-severity anomalies:")
    for a in report["anomalies"]:
        if a["severity"] == "high":
            print(f"  [{a['date']}] {a['anomaly_type'].upper()}: {a['description'][:90]}...")