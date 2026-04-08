"""
KairosAI — Test Fixtures (conftest.py)
----------------------------------------
Shared fixtures used across all test modules.
Mocks the Groq/OpenAI client so tests run without API keys.
"""

import sys
import os
import types
import pytest

# ── Add backend to path ───────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── Mock Groq (OpenAI-compatible) client ──────────────────────────────────────

def _make_mock_response(text: str):
    """Build a fake OpenAI chat completion response object."""
    class FakeMessage:
        content = text

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    return FakeResponse()


MOCK_AGENT_JSON = """{
  "verdict": "ROLL_BACK",
  "confidence": 85,
  "summary": "Three SLO breaches confirmed. Crash rate at 2.4/1000, p95 latency 352ms, D1 retention dropped 5.8pp.",
  "key_findings": [
    "Crash rate 2.4/1000 — breaches 2.0 threshold",
    "p95 latency 352ms — breaches 300ms SLO",
    "D1 retention 56.0% — dropped 5.8pp from baseline"
  ],
  "risks": [
    {"risk": "iOS crash on dashboard load", "severity": "critical", "mitigation": "Rollback feature flag immediately"},
    {"risk": "Duplicate payment charges", "severity": "critical", "mitigation": "Audit all transactions"}
  ],
  "recommended_actions": [
    {"action": "Toggle SMARTDASH_V2 to OFF", "owner": "Engineering", "priority": "P0", "timeframe": "immediate"},
    {"action": "Initiate payment refund process", "owner": "Payments Team", "priority": "P0", "timeframe": "immediate"}
  ]
}"""

MOCK_MODERATOR_JSON = """{
  "consensus_exists": false,
  "tension": "PM wants to PAUSE for recovery; Risk and SRE demand ROLL_BACK on payment integrity alone.",
  "side_a": {
    "agents": ["Data Analyst", "Marketing / Comms"],
    "verdict": "PAUSE",
    "strongest_argument": "Partial recovery visible over last 2 days suggests hot-patch is working."
  },
  "side_b": {
    "agents": ["Product Manager", "SRE / Engineering", "Risk / Critic"],
    "verdict": "ROLL_BACK",
    "strongest_argument": "Three simultaneous SLO breaches plus unresolved payment integrity risk."
  },
  "evidence_gap": "Whether 2-day recovery trend is statistically significant or noise.",
  "ruling": "Side B has stronger evidence. Three simultaneous SLO breaches is a hard rollback signal per SRE rules.",
  "resolved_verdict": "ROLL_BACK",
  "resolved_confidence": 88,
  "key_unresolved_question": "Will the iOS hot-patch fully resolve the crash within 72 hours?"
}"""


@pytest.fixture
def mock_openai(monkeypatch):
    """
    Patch the openai module with a fake client that returns
    MOCK_AGENT_JSON for all chat.completions.create() calls.
    """
    mock_mod = types.ModuleType('openai')

    class FakeCompletions:
        @staticmethod
        def create(**kwargs):
            # Return moderator JSON for moderator calls (longer max_tokens)
            if kwargs.get('max_tokens', 0) == 1000:
                return _make_mock_response(MOCK_MODERATOR_JSON)
            return _make_mock_response(MOCK_AGENT_JSON)

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    mock_mod.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, 'openai', mock_mod)

    mock_dotenv = types.ModuleType('dotenv')
    mock_dotenv.load_dotenv = lambda: None
    monkeypatch.setitem(sys.modules, 'dotenv', mock_dotenv)

    return mock_mod


@pytest.fixture
def sample_agent_report():
    """A realistic AgentReport-like dict for use in multiple tests."""
    return {
        "agent_name":          "Data Analyst",
        "role":                "Data Analyst — metrics, trends, anomalies",
        "verdict":             "ROLL_BACK",
        "confidence":          85,
        "summary":             "Three SLO breaches confirmed with statistical significance.",
        "key_findings":        ["Crash rate 3x baseline", "p95 latency 352ms"],
        "risks":               [{"risk": "iOS crash", "severity": "critical", "mitigation": "Rollback"}],
        "recommended_actions": [{"action": "Toggle flag", "owner": "Engineering", "priority": "P0", "timeframe": "immediate"}],
        "tool_calls_made":     ["aggregate_metrics", "detect_anomalies"],
        "timestamp":           "2025-07-14T10:00:00",
    }


@pytest.fixture
def all_verdicts_rollback(mock_openai):
    """
    Returns 5 mock AgentReport objects all voting ROLL_BACK.
    Requires mock_openai to avoid importing anthropic.
    """
    # Import after mock is in place
    from agents.base import AgentReport

    reports = []
    for name, conf in [
        ("Data Analyst",      80),
        ("Product Manager",   90),
        ("Marketing / Comms", 75),
        ("SRE / Engineering", 90),
        ("Risk / Critic",     95),
    ]:
        r = AgentReport(
            agent_name=name, role=name,
            verdict="ROLL_BACK", confidence=conf,
            summary="SLOs breached.",
            key_findings=["Crash rate above threshold"],
            risks=[], recommended_actions=[],
            tool_calls_made=[],
        )
        reports.append(r)
    return reports