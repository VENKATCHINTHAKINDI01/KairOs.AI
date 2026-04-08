"""
KairosAI — Orchestrator & Core Integration Tests
--------------------------------------------------
Tests the confidence scorer, session memory, debate engine,
and output layer without making real API calls.
"""

import pytest
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── SessionMemory ─────────────────────────────────────────────────────────────

class TestSessionMemory:

    def test_initial_state_is_empty(self):
        from core.session_memory import SessionMemory
        mem = SessionMemory("test-001")
        assert len(mem.get_all_events()) == 0

    def test_log_orchestrator_note(self):
        from core.session_memory import SessionMemory
        mem = SessionMemory("test-002")
        mem.log_orchestrator_note("War room started")
        events = mem.get_all_events()
        assert len(events) == 1
        assert events[0]["type"] == "orchestrator_note"
        assert events[0]["note"] == "War room started"

    def test_log_tool_result(self):
        from core.session_memory import SessionMemory
        mem = SessionMemory("test-003")
        mem.log_tool_result("Analyst", "aggregate_metrics", {"health": "degraded"})
        events = mem.get_all_events()
        assert events[0]["type"] == "tool_result"
        assert events[0]["tool"] == "aggregate_metrics"

    def test_log_agent_report(self, sample_agent_report):
        from core.session_memory import SessionMemory

        class FakeReport:
            def to_dict(self): return sample_agent_report

        mem = SessionMemory("test-004")
        mem.log_agent_report(FakeReport())
        reports = mem.get_agent_reports()
        assert len(reports) == 1
        assert reports[0]["agent_name"] == "Data Analyst"

    def test_log_debate(self):
        from core.session_memory import SessionMemory
        mem = SessionMemory("test-005")
        mem.log_debate({"resolved_verdict": "ROLL_BACK", "resolved_confidence": 88})
        debate = mem.get_debate()
        assert debate is not None
        assert debate["resolved_verdict"] == "ROLL_BACK"

    def test_log_final_decision_sets_finished_at(self):
        from core.session_memory import SessionMemory
        mem = SessionMemory("test-006")
        mem.log_final_decision({"decision": "ROLL_BACK", "confidence": {"weighted_score": 87}})
        assert mem.finished_at is not None

    def test_get_verdicts(self, sample_agent_report):
        from core.session_memory import SessionMemory

        class FakeReport:
            def to_dict(self): return sample_agent_report

        mem = SessionMemory("test-007")
        mem.log_agent_report(FakeReport())
        verdicts = mem.get_verdicts()
        assert verdicts[0]["agent"] == "Data Analyst"
        assert verdicts[0]["verdict"] == "ROLL_BACK"

    def test_events_have_timestamps(self):
        from core.session_memory import SessionMemory
        mem = SessionMemory("test-008")
        mem.log_orchestrator_note("test")
        event = mem.get_all_events()[0]
        assert "timestamp" in event
        assert "seq" in event
        assert event["seq"] == 1

    def test_sequence_numbers_increment(self):
        from core.session_memory import SessionMemory
        mem = SessionMemory("test-009")
        for i in range(3):
            mem.log_orchestrator_note(f"note {i}")
        events = mem.get_all_events()
        seqs = [e["seq"] for e in events]
        assert seqs == [1, 2, 3]

    def test_to_dict_structure(self):
        from core.session_memory import SessionMemory
        mem = SessionMemory("test-010")
        d = mem.to_dict()
        assert "session_id" in d
        assert "started_at" in d
        assert "events" in d
        assert d["session_id"] == "test-010"


# ── Confidence Scorer ─────────────────────────────────────────────────────────

class TestConfidenceScorer:

    def _make_report(self, name, verdict, confidence):
        class R:
            pass
        r = R()
        r.agent_name = name
        r.verdict    = verdict
        r.confidence = confidence
        return r

    def test_returns_weighted_score(self):
        from core.confidence_scorer import compute_confidence
        reports = [
            self._make_report("Data Analyst",      "ROLL_BACK", 80),
            self._make_report("SRE / Engineering", "ROLL_BACK", 75),
            self._make_report("Product Manager",   "PAUSE",     65),
            self._make_report("Marketing / Comms", "PAUSE",     60),
            self._make_report("Risk / Critic",     "ROLL_BACK", 85),
        ]
        result = compute_confidence(reports)
        assert "weighted_score" in result
        assert 0 <= result["weighted_score"] <= 100

    def test_perfect_consensus_adds_bonus(self):
        from core.confidence_scorer import compute_confidence
        reports = [self._make_report(f"Agent {i}", "ROLL_BACK", 80) for i in range(5)]
        result = compute_confidence(reports)
        assert result["agreement_bonus"] == 8
        assert result["agreement_penalty"] == 0

    def test_split_vote_adds_penalty(self):
        from core.confidence_scorer import compute_confidence
        reports = [
            self._make_report("Agent 1", "PROCEED",   80),
            self._make_report("Agent 2", "PAUSE",     80),
            self._make_report("Agent 3", "ROLL_BACK", 80),
        ]
        result = compute_confidence(reports)
        assert result["agreement_penalty"] > 0

    def test_verdict_distribution_correct(self):
        from core.confidence_scorer import compute_confidence
        reports = [
            self._make_report("A1", "ROLL_BACK", 80),
            self._make_report("A2", "ROLL_BACK", 75),
            self._make_report("A3", "PAUSE",     65),
        ]
        result = compute_confidence(reports)
        dist = result["verdict_distribution"]
        assert dist["ROLL_BACK"] == 2
        assert dist["PAUSE"] == 1

    def test_includes_debate_moderator_when_provided(self):
        from core.confidence_scorer import compute_confidence
        reports = [self._make_report("Data Analyst", "ROLL_BACK", 80)]
        debate = {"resolved_verdict": "ROLL_BACK", "resolved_confidence": 90}
        result = compute_confidence(reports, debate)
        agents = [p["agent"] for p in result["per_agent"]]
        assert "Debate Moderator" in agents

    def test_empty_reports_returns_error(self):
        from core.confidence_scorer import compute_confidence
        result = compute_confidence([])
        assert "error" in result

    def test_interpretation_field_present(self):
        from core.confidence_scorer import compute_confidence
        reports = [self._make_report("Data Analyst", "ROLL_BACK", 85)]
        result = compute_confidence(reports)
        assert "interpretation" in result
        assert len(result["interpretation"]) > 0

    def test_confidence_boosters_present(self):
        from core.confidence_scorer import compute_confidence
        reports = [self._make_report("Data Analyst", "ROLL_BACK", 85)]
        result = compute_confidence(reports)
        assert "confidence_boosters" in result
        assert isinstance(result["confidence_boosters"], list)

    def test_high_agreement_high_score(self):
        from core.confidence_scorer import compute_confidence
        # All agents agree with high confidence → high score
        reports = [self._make_report(f"A{i}", "ROLL_BACK", 90) for i in range(5)]
        result = compute_confidence(reports)
        assert result["weighted_score"] >= 90, \
            f"Expected ≥90 with perfect consensus at 90 confidence, got {result['weighted_score']}"


# ── Output Layer ──────────────────────────────────────────────────────────────

class TestJSONWriter:

    @pytest.fixture
    def sample_decision(self):
        return {
            "meta": {
                "session_id":   "test-write-001",
                "product":      "PurpleMerit SmartDash 2.0",
                "generated_at": "2025-07-14T10:00:00Z",
                "agents_run":   ["Data Analyst", "PM"],
            },
            "decision":  "ROLL_BACK",
            "confidence": {"weighted_score": 87, "interpretation": "High confidence."},
            "rationale":  {"primary_drivers": ["Crash rate 3x baseline"]},
            "risk_register":  [{"risk": "iOS crash", "severity": "critical", "mitigation": "Rollback"}],
            "action_plan":    {"immediate": [{"action": "Toggle flag", "owner": "Eng", "priority": "P0", "timeframe": "immediate"}], "within_24h": [], "within_48h": []},
            "communication_plan": {"internal_message": "Rolling back.", "user_message": "Investigating.", "enterprise_message": "Reaching out."},
            "agent_verdicts": [],
            "debate_summary": {"tension": "PM vs Risk", "consensus_exists": False, "resolved_verdict": "ROLL_BACK", "resolved_confidence": 88, "key_unresolved": "?"},
            "session_stats":  {"total_agents": 5, "verdict_tally": {"ROLL_BACK": 3, "PAUSE": 2}, "avg_confidence": 85.0, "total_events": 20},
        }

    def test_json_file_created(self, tmp_path, sample_decision):
        from output.json_writer import write_json_report
        path = write_json_report(sample_decision, str(tmp_path))
        assert os.path.exists(path)

    def test_json_file_is_valid(self, tmp_path, sample_decision):
        from output.json_writer import write_json_report
        path = write_json_report(sample_decision, str(tmp_path))
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["decision"] == "ROLL_BACK"

    def test_json_filename_contains_session_id(self, tmp_path, sample_decision):
        from output.json_writer import write_json_report
        path = write_json_report(sample_decision, str(tmp_path))
        assert "test-write-001" in os.path.basename(path)

    def test_json_file_size_nonzero(self, tmp_path, sample_decision):
        from output.json_writer import write_json_report
        path = write_json_report(sample_decision, str(tmp_path))
        assert os.path.getsize(path) > 100


class TestMarkdownWriter:

    @pytest.fixture
    def sample_decision(self):
        return {
            "meta": {
                "session_id":   "test-md-001",
                "product":      "PurpleMerit SmartDash 2.0",
                "generated_at": "2025-07-14T10:00:00Z",
                "agents_run":   ["Data Analyst"],
            },
            "decision":  "ROLL_BACK",
            "confidence": {"weighted_score": 87, "interpretation": "High confidence.", "verdict_distribution": {"ROLL_BACK": 3, "PAUSE": 2}, "agreement_ratio": 0.6, "per_agent": [], "boosters": ["More data needed."]},
            "rationale":  {"primary_drivers": ["Crash rate 3x baseline"], "metric_references": ["Crash: 2.4/1000"], "feedback_summary": "Negative dominant.", "debate_resolution": "Risk wins."},
            "risk_register": [{"risk": "iOS crash", "severity": "critical", "mitigation": "Rollback", "owner": "Mobile", "source_agent": "SRE"}],
            "action_plan": {"immediate": [{"action": "Toggle flag", "owner": "Eng", "priority": "P0", "timeframe": "immediate", "source_agent": "SRE"}], "within_24h": [], "within_48h": []},
            "communication_plan": {"internal_message": "Rolling back.", "user_message": "Investigating.", "enterprise_message": "Reaching out."},
            "agent_verdicts": [{"agent_name": "Data Analyst", "verdict": "ROLL_BACK", "confidence": 85, "summary": "Three SLOs breached."}],
            "debate_summary": {"tension": "PM vs Risk", "consensus_exists": False, "resolved_verdict": "ROLL_BACK", "resolved_confidence": 88, "key_unresolved": "Will patch work?"},
            "session_stats": {"total_agents": 5, "verdict_tally": {"ROLL_BACK": 3, "PAUSE": 2}, "avg_confidence": 85.0, "total_events": 20},
        }

    def test_markdown_file_created(self, tmp_path, sample_decision):
        from output.markdown_writer import write_markdown_report
        path = write_markdown_report(sample_decision, str(tmp_path))
        assert os.path.exists(path)
        assert path.endswith(".md")

    def test_markdown_contains_verdict(self, tmp_path, sample_decision):
        from output.markdown_writer import write_markdown_report
        path = write_markdown_report(sample_decision, str(tmp_path))
        content = open(path).read()
        assert "ROLL BACK" in content

    def test_markdown_contains_risk_register_section(self, tmp_path, sample_decision):
        from output.markdown_writer import write_markdown_report
        path = write_markdown_report(sample_decision, str(tmp_path))
        content = open(path).read()
        assert "Risk Register" in content

    def test_markdown_contains_action_plan(self, tmp_path, sample_decision):
        from output.markdown_writer import write_markdown_report
        path = write_markdown_report(sample_decision, str(tmp_path))
        content = open(path).read()
        assert "Action Plan" in content

    def test_markdown_contains_agent_verdicts(self, tmp_path, sample_decision):
        from output.markdown_writer import write_markdown_report
        path = write_markdown_report(sample_decision, str(tmp_path))
        content = open(path).read()
        assert "Agent Verdicts" in content

    def test_markdown_contains_communication_plan(self, tmp_path, sample_decision):
        from output.markdown_writer import write_markdown_report
        path = write_markdown_report(sample_decision, str(tmp_path))
        content = open(path).read()
        assert "Communication Plan" in content


class TestReportBuilder:

    @pytest.fixture
    def minimal_decision(self):
        return {
            "meta": {"session_id": "build-001", "product": "Test", "generated_at": "2025Z", "agents_run": []},
            "decision": "PAUSE",
            "confidence": {"weighted_score": 65, "interpretation": "Moderate.", "verdict_distribution": {}, "agreement_ratio": 0.5, "per_agent": [], "boosters": []},
            "rationale": {"primary_drivers": [], "metric_references": [], "feedback_summary": "", "debate_resolution": ""},
            "risk_register": [],
            "action_plan": {"immediate": [], "within_24h": [], "within_48h": []},
            "communication_plan": {"internal_message": ".", "user_message": ".", "enterprise_message": "."},
            "agent_verdicts": [],
            "debate_summary": {"tension": "", "consensus_exists": True, "resolved_verdict": "PAUSE", "resolved_confidence": 65, "key_unresolved": ""},
            "session_stats": {"total_agents": 2, "verdict_tally": {}, "avg_confidence": 65.0, "total_events": 5},
        }

    def test_build_report_returns_paths(self, tmp_path, minimal_decision):
        from output.report_builder import build_report
        result = build_report(minimal_decision, str(tmp_path))
        assert "json_report" in result
        assert "markdown_report" in result

    def test_both_files_exist(self, tmp_path, minimal_decision):
        from output.report_builder import build_report
        result = build_report(minimal_decision, str(tmp_path))
        assert os.path.exists(result["json_report"])
        assert os.path.exists(result["markdown_report"])

    def test_result_contains_verdict(self, tmp_path, minimal_decision):
        from output.report_builder import build_report
        result = build_report(minimal_decision, str(tmp_path))
        assert result["verdict"] == "PAUSE"

    def test_result_contains_confidence(self, tmp_path, minimal_decision):
        from output.report_builder import build_report
        result = build_report(minimal_decision, str(tmp_path))
        assert result["confidence"] == 65


# ── Data Layer ────────────────────────────────────────────────────────────────

class TestDataLayer:
    """Smoke tests confirming mock data loads correctly."""

    def test_metrics_has_ten_days(self):
        from data.metrics import get_all
        assert len(get_all()) == 10

    def test_feedback_has_35_entries(self):
        from data.feedback import get_all
        assert len(get_all()) == 35

    def test_feedback_majority_negative(self):
        from data.feedback import get_summary_stats
        stats = get_summary_stats()
        assert stats["negative_pct"] > 50

    def test_release_notes_has_critical_issues(self):
        from data.release_notes import get_critical_issues
        critical = get_critical_issues()
        assert len(critical) >= 2

    def test_success_criteria_are_breached(self):
        from data.release_notes import get_success_criteria
        criteria = get_success_criteria()
        assert "breached" in criteria["current_verdict"].lower()

    def test_baseline_is_three_days(self):
        from data.metrics import get_baseline
        assert len(get_baseline()) == 3

    def test_post_launch_is_seven_days(self):
        from data.metrics import get_post_launch
        assert len(get_post_launch()) == 7

    def test_kpi_thresholds_defined(self):
        from data.metrics import KPI_THRESHOLDS
        assert "crash_rate" in KPI_THRESHOLDS
        assert "p95_latency_ms" in KPI_THRESHOLDS
        assert "payment_success_rate" in KPI_THRESHOLDS