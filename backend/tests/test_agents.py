"""
KairosAI — Agent Unit Tests
------------------------------
Tests agent structure, tool dispatch, JSON parsing, and report output.
Uses mock_openai fixture — no real API calls made.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── Base Agent & AgentReport ──────────────────────────────────────────────────

class TestAgentReport:

    def test_to_dict_has_all_fields(self, mock_openai):
        from agents.base import AgentReport
        r = AgentReport(
            agent_name="Test Agent", role="Tester",
            verdict="PAUSE", confidence=70,
            summary="Test summary.",
            key_findings=["Finding 1", "Finding 2"],
            risks=[{"risk": "test risk", "severity": "high", "mitigation": "fix it"}],
            recommended_actions=[{"action": "do this", "owner": "Team", "priority": "P0", "timeframe": "immediate"}],
            tool_calls_made=["aggregate_metrics"],
        )
        d = r.to_dict()
        required = {"agent_name", "role", "verdict", "confidence", "summary",
                    "key_findings", "risks", "recommended_actions",
                    "tool_calls_made", "timestamp"}
        assert required.issubset(d.keys())

    def test_verdict_stored_correctly(self, mock_openai):
        from agents.base import AgentReport
        for verdict in ("PROCEED", "PAUSE", "ROLL_BACK"):
            r = AgentReport(
                agent_name="X", role="X", verdict=verdict, confidence=80,
                summary="", key_findings=[], risks=[], recommended_actions=[],
                tool_calls_made=[],
            )
            assert r.verdict == verdict

    def test_timestamp_is_set(self, mock_openai):
        from agents.base import AgentReport
        r = AgentReport(
            agent_name="X", role="X", verdict="PAUSE", confidence=50,
            summary="", key_findings=[], risks=[], recommended_actions=[],
            tool_calls_made=[],
        )
        assert r.timestamp is not None
        assert len(r.timestamp) > 0


class TestBaseAgentJsonParsing:

    def test_parses_clean_json(self, mock_openai):
        from agents.base import BaseAgent
        agent = BaseAgent()
        raw = '{"verdict": "ROLL_BACK", "confidence": 85, "summary": "test", "key_findings": [], "risks": [], "recommended_actions": []}'
        result = agent._parse_response(raw)
        assert result["verdict"] == "ROLL_BACK"
        assert result["confidence"] == 85

    def test_strips_markdown_fences(self, mock_openai):
        from agents.base import BaseAgent
        agent = BaseAgent()
        raw = '```json\n{"verdict": "PAUSE", "confidence": 70, "summary": "test", "key_findings": [], "risks": [], "recommended_actions": []}\n```'
        result = agent._parse_response(raw)
        assert result["verdict"] == "PAUSE"

    def test_fallback_on_invalid_json(self, mock_openai):
        from agents.base import BaseAgent
        agent = BaseAgent()
        result = agent._parse_response("This is not JSON at all")
        assert result["verdict"] == "PAUSE"
        assert result["confidence"] == 50

    def test_extracts_json_from_prose(self, mock_openai):
        from agents.base import BaseAgent
        agent = BaseAgent()
        raw = 'Here is my analysis: {"verdict": "ROLL_BACK", "confidence": 90, "summary": "s", "key_findings": [], "risks": [], "recommended_actions": []}'
        result = agent._parse_response(raw)
        assert result["verdict"] == "ROLL_BACK"


# ── Individual Agents — structure & tool assignment ───────────────────────────

class TestPMAgent:

    def test_tools_assigned(self, mock_openai):
        from agents.pm import PMAgent
        a = PMAgent()
        assert "aggregate_metrics" in a.tools_to_use
        assert "trend_compare" in a.tools_to_use

    def test_run_returns_agent_report(self, mock_openai):
        from agents.pm import PMAgent
        from agents.base import AgentReport
        a = PMAgent()
        report = a.run()
        assert isinstance(report, AgentReport)

    def test_report_has_valid_verdict(self, mock_openai):
        from agents.pm import PMAgent
        report = PMAgent().run()
        assert report.verdict in ("PROCEED", "PAUSE", "ROLL_BACK")

    def test_report_confidence_in_range(self, mock_openai):
        from agents.pm import PMAgent
        report = PMAgent().run()
        assert 0 <= report.confidence <= 100

    def test_tool_calls_recorded(self, mock_openai):
        from agents.pm import PMAgent
        report = PMAgent().run()
        assert len(report.tool_calls_made) > 0


class TestAnalystAgent:

    def test_uses_three_tools(self, mock_openai):
        from agents.analyst import AnalystAgent
        a = AnalystAgent()
        assert len(a.tools_to_use) == 3

    def test_run_returns_valid_report(self, mock_openai):
        from agents.analyst import AnalystAgent
        from agents.base import AgentReport
        report = AnalystAgent().run()
        assert isinstance(report, AgentReport)
        assert report.verdict in ("PROCEED", "PAUSE", "ROLL_BACK")

    def test_has_key_findings(self, mock_openai):
        from agents.analyst import AnalystAgent
        report = AnalystAgent().run()
        assert isinstance(report.key_findings, list)

    def test_has_risks(self, mock_openai):
        from agents.analyst import AnalystAgent
        report = AnalystAgent().run()
        assert isinstance(report.risks, list)


class TestMarketingAgent:

    def test_uses_sentiment_tool(self, mock_openai):
        from agents.marketing import MarketingAgent
        a = MarketingAgent()
        assert "sentiment_analyzer" in a.tools_to_use

    def test_run_returns_report(self, mock_openai):
        from agents.marketing import MarketingAgent
        from agents.base import AgentReport
        report = MarketingAgent().run()
        assert isinstance(report, AgentReport)

    def test_communication_plan_attached(self, mock_openai):
        from agents.marketing import MarketingAgent
        report = MarketingAgent().run()
        # Marketing agent attaches communication_plan to the report
        assert hasattr(report, 'communication_plan')


class TestRiskAgent:

    def test_tools_assigned(self, mock_openai):
        from agents.risk import RiskAgent
        a = RiskAgent()
        assert "risk_scorer" in a.tools_to_use
        assert "detect_anomalies" in a.tools_to_use

    def test_run_returns_report(self, mock_openai):
        from agents.risk import RiskAgent
        from agents.base import AgentReport
        report = RiskAgent().run()
        assert isinstance(report, AgentReport)

    def test_challenges_attached(self, mock_openai):
        from agents.risk import RiskAgent
        report = RiskAgent().run()
        assert hasattr(report, 'challenges')
        assert isinstance(report.challenges, list)

    def test_evidence_requests_attached(self, mock_openai):
        from agents.risk import RiskAgent
        report = RiskAgent().run()
        assert hasattr(report, 'evidence_requests')


class TestSREAgent:

    def test_tools_assigned(self, mock_openai):
        from agents.sre import SREAgent
        a = SREAgent()
        assert "aggregate_metrics" in a.tools_to_use
        assert "detect_anomalies" in a.tools_to_use

    def test_run_returns_report(self, mock_openai):
        from agents.sre import SREAgent
        from agents.base import AgentReport
        report = SREAgent().run()
        assert isinstance(report, AgentReport)

    def test_slo_status_attached(self, mock_openai):
        from agents.sre import SREAgent
        report = SREAgent().run()
        assert hasattr(report, 'slo_status')
        assert isinstance(report.slo_status, dict)

    def test_root_cause_hypothesis_attached(self, mock_openai):
        from agents.sre import SREAgent
        report = SREAgent().run()
        assert hasattr(report, 'root_cause_hypothesis')


# ── MonitorAgent ──────────────────────────────────────────────────────────────

class TestMonitorAgent:

    def test_initial_tally_is_zero(self, mock_openai):
        from agents.monitor import MonitorAgent
        m = MonitorAgent()
        tally = m.get_verdict_tally()
        assert tally == {"PROCEED": 0, "PAUSE": 0, "ROLL_BACK": 0}

    def test_ingest_updates_tally(self, mock_openai):
        from agents.monitor import MonitorAgent
        from agents.base import AgentReport
        m = MonitorAgent()

        class FakeReport:
            def to_dict(self):
                return {"agent_name": "Data Analyst", "verdict": "ROLL_BACK",
                        "confidence": 80, "summary": "Test", "key_findings": [],
                        "risks": [], "recommended_actions": [], "tool_calls_made": [], "timestamp": ""}

        m.ingest(FakeReport())
        assert m.get_verdict_tally()["ROLL_BACK"] == 1

    def test_get_current_consensus(self, mock_openai):
        from agents.monitor import MonitorAgent
        from agents.base import AgentReport
        m = MonitorAgent()

        for verdict in ("ROLL_BACK", "ROLL_BACK", "PAUSE"):
            class FakeReport:
                def __init__(self, v):
                    self._v = v
                def to_dict(self):
                    return {"agent_name": "Agent", "verdict": self._v,
                            "confidence": 80, "summary": "", "key_findings": [],
                            "risks": [], "recommended_actions": [], "tool_calls_made": [], "timestamp": ""}
            m.ingest(FakeReport(verdict))

        assert m.get_current_consensus() == "ROLL_BACK"

    def test_avg_confidence_calculation(self, mock_openai):
        from agents.monitor import MonitorAgent
        m = MonitorAgent()

        for conf in (80, 90, 70):
            class FR:
                def __init__(self, c): self._c = c
                def to_dict(self):
                    return {"agent_name": "A", "verdict": "PAUSE", "confidence": self._c,
                            "summary": "", "key_findings": [], "risks": [],
                            "recommended_actions": [], "tool_calls_made": [], "timestamp": ""}
            m.ingest(FR(conf))

        assert m.get_avg_confidence() == 80.0

    def test_session_summary_structure(self, mock_openai):
        from agents.monitor import MonitorAgent
        m = MonitorAgent()
        summary = m.get_session_summary()
        required = {"agents_reported", "verdict_tally", "current_consensus",
                    "avg_confidence", "confidence_by_agent"}
        assert required.issubset(summary.keys())