"""
KairosAI — Tool Unit Tests
----------------------------
Tests every tool function in isolation against the mock data.
No API calls required — tools are pure Python.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── aggregate_metrics ─────────────────────────────────────────────────────────

class TestAggregateMetrics:

    def setup_method(self):
        from tools.aggregate_metrics import aggregate_metrics
        self.tool = aggregate_metrics

    def test_returns_overall_health(self):
        result = self.tool()
        assert "overall_health" in result
        assert result["overall_health"] in ("healthy", "degraded", "critical")

    def test_health_is_degraded_for_post_launch(self):
        """Post-launch data has multiple breaches — must not be healthy."""
        result = self.tool()
        assert result["overall_health"] != "healthy"

    def test_returns_kpi_summaries(self):
        result = self.tool()
        assert "summaries" in result
        assert len(result["summaries"]) > 0

    def test_each_summary_has_required_fields(self):
        result = self.tool()
        required = {"kpi", "baseline_avg", "current_value", "pct_change", "status", "trend"}
        for summary in result["summaries"]:
            assert required.issubset(summary.keys()), f"Missing keys in {summary['kpi']}"

    def test_status_values_are_valid(self):
        result = self.tool()
        valid = {"OK", "WARN", "CRITICAL"}
        for s in result["summaries"]:
            assert s["status"] in valid, f"Invalid status '{s['status']}' for {s['kpi']}"

    def test_trend_values_are_valid(self):
        result = self.tool()
        valid = {"improving", "stable", "degrading"}
        for s in result["summaries"]:
            assert s["trend"] in valid

    def test_crash_rate_is_critical_or_warn(self):
        result = self.tool()
        crash = next((s for s in result["summaries"] if s["kpi"] == "crash_rate"), None)
        assert crash is not None
        assert crash["status"] in ("WARN", "CRITICAL"), \
            f"Crash rate {crash['current_value']} should be WARN or CRITICAL"

    def test_counts_sum_to_total(self):
        result = self.tool()
        total = result["ok_count"] + result["warn_count"] + result["critical_count"]
        assert total == result["total_kpis"]

    def test_critical_kpis_list_is_populated(self):
        result = self.tool()
        # With current data, at least one KPI should be critical
        # (support tickets are at 128, threshold is 120)
        assert isinstance(result["critical_kpis"], list)

    def test_pct_change_is_numeric(self):
        result = self.tool()
        for s in result["summaries"]:
            assert isinstance(s["pct_change"], (int, float))


# ── detect_anomalies ──────────────────────────────────────────────────────────

class TestDetectAnomalies:

    def setup_method(self):
        from tools.detect_anomalies import detect_anomalies
        self.tool = detect_anomalies

    def test_returns_anomalies_list(self):
        result = self.tool()
        assert "anomalies" in result
        assert isinstance(result["anomalies"], list)

    def test_detects_anomalies_post_launch(self):
        result = self.tool()
        assert result["total_anomalies"] > 0, "Should detect anomalies in degraded post-launch data"

    def test_high_severity_count_is_significant(self):
        result = self.tool()
        assert result["high_severity"] > 5, \
            f"Expected many high-severity anomalies, got {result['high_severity']}"

    def test_anomaly_start_date_is_after_launch(self):
        result = self.tool()
        # Launch was July 7, anomalies should start around then
        start = result.get("anomaly_start_date", "")
        assert start >= "2025-07-04", f"Anomaly start {start} seems too early"

    def test_each_anomaly_has_required_fields(self):
        result = self.tool()
        required = {"kpi", "date", "value"}
        for anomaly in result["anomalies"][:5]:
            assert required.issubset(anomaly.keys()), f"Anomaly missing keys: {anomaly}"

    def test_crash_rate_in_most_anomalous(self):
        result = self.tool()
        top_kpis = result.get("most_anomalous_kpis", [])
        assert "crash_rate" in top_kpis, \
            f"crash_rate should be in most anomalous KPIs, got {top_kpis}"

    def test_consecutive_breach_kpis_is_list(self):
        result = self.tool()
        assert isinstance(result["consecutive_breach_kpis"], list)


# ── sentiment_analyzer ────────────────────────────────────────────────────────

class TestSentimentAnalyzer:

    def setup_method(self):
        from tools.sentiment_analyzer import sentiment_analyzer
        self.tool = sentiment_analyzer

    def test_returns_overall_score(self):
        result = self.tool()
        assert "overall_score" in result
        assert -1.0 <= result["overall_score"] <= 1.0

    def test_score_is_negative_for_bad_launch(self):
        result = self.tool()
        assert result["overall_score"] < 0, \
            f"54% negative feedback should produce negative score, got {result['overall_score']}"

    def test_dominant_sentiment_is_negative(self):
        result = self.tool()
        assert result["dominant_sentiment"] == "negative"

    def test_total_entries_matches_dataset(self):
        result = self.tool()
        assert result["total_entries"] == 35, \
            f"Expected 35 feedback entries, got {result['total_entries']}"

    def test_distribution_sums_to_total(self):
        result = self.tool()
        dist = result["distribution"]
        total = dist.get("positive", 0) + dist.get("neutral", 0) + dist.get("negative", 0)
        assert total == result["total_entries"]

    def test_critical_signals_contains_churn(self):
        result = self.tool()
        signals = result.get("critical_signals", [])
        assert len(signals) > 0, "Should have critical signals (payment, churn)"

    def test_verbatim_highlights_present(self):
        result = self.tool()
        assert "verbatim_highlights" in result
        vh = result["verbatim_highlights"]
        assert isinstance(vh, dict)
        assert "most_negative" in vh or "most_positive" in vh

    def test_enterprise_negative_pct_is_high(self):
        result = self.tool()
        # Enterprise users have multiple critical complaints
        pct = result.get("enterprise_negative_pct", 0)
        assert pct > 0, "Enterprise negative % should be > 0"


# ── trend_compare ─────────────────────────────────────────────────────────────

class TestTrendCompare:

    def setup_method(self):
        from tools.trend_compare import trend_compare
        self.tool = trend_compare

    def test_returns_launch_impact_verdict(self):
        result = self.tool()
        assert "launch_impact_verdict" in result
        assert result["launch_impact_verdict"] in ("minimal", "moderate", "significant", "severe")

    def test_verdict_is_severe(self):
        result = self.tool()
        assert result["launch_impact_verdict"] == "severe", \
            f"Expected 'severe' for this data, got '{result['launch_impact_verdict']}'"

    def test_worst_kpi_is_crash_or_tickets(self):
        result = self.tool()
        assert result["worst_kpi"] in ("crash_rate", "support_tickets", "error_rate"), \
            f"Unexpected worst KPI: {result['worst_kpi']}"

    def test_comparisons_list_is_populated(self):
        result = self.tool()
        assert "comparisons" in result
        assert len(result["comparisons"]) > 0

    def test_each_comparison_has_pct_change(self):
        result = self.tool()
        for comp in result["comparisons"]:
            # actual key is baseline_to_current_pct
            assert "baseline_to_current_pct" in comp, f"Missing baseline_to_current_pct in {comp}"
            assert isinstance(comp["baseline_to_current_pct"], (int, float))

    def test_degraded_kpis_count_positive(self):
        result = self.tool()
        degraded = result.get("kpis_still_degraded", [])
        assert len(degraded) > 0, "Should have multiple degraded KPIs post-launch"


# ── risk_scorer ───────────────────────────────────────────────────────────────

class TestRiskScorer:

    def setup_method(self):
        from tools.risk_scorer import risk_scorer
        self.tool = risk_scorer

    def test_returns_risks_list(self):
        result = self.tool()
        assert "risks" in result
        assert isinstance(result["risks"], list)

    def test_has_at_least_five_risks(self):
        result = self.tool()
        assert result["total_risks"] >= 5, \
            f"Expected at least 5 risks, got {result['total_risks']}"

    def test_recommended_posture_is_rollback(self):
        result = self.tool()
        assert result["recommended_posture"] == "rollback", \
            f"Expected rollback posture, got '{result['recommended_posture']}'"

    def test_each_risk_has_required_fields(self):
        result = self.tool()
        # actual keys: id, category, title, description, likelihood, impact, score, rating, mitigation
        required = {"title", "description", "mitigation", "rating"}
        for risk in result["risks"]:
            missing = required - risk.keys()
            assert not missing, f"Risk missing fields {missing}: {risk.get('title','?')}"

    def test_severity_values_are_valid(self):
        result = self.tool()
        valid = {"critical", "high", "medium", "low"}
        for risk in result["risks"]:
            assert risk["rating"] in valid, \
                f"Invalid rating '{risk['rating']}' in risk '{risk.get('title','?')}'"

    def test_critical_risks_exist(self):
        result = self.tool()
        critical = [r for r in result["risks"] if r["rating"] == "critical"]
        assert len(critical) > 0, "Should have at least one critical risk"

    def test_top_risks_is_populated(self):
        result = self.tool()
        assert "top_risks" in result
        assert len(result["top_risks"]) > 0

    def test_risk_counts_sum_correctly(self):
        result = self.tool()
        total = (result["critical_count"] + result["high_count"] +
                 result["medium_count"] + result["low_count"])
        assert total == result["total_risks"]