"""
KairosAI — Session Memory
---------------------------
Central store for the entire war room session.
Every agent report, tool result, debate exchange, and
orchestrator note gets written here.

The MonitorAgent reads from this to answer questions.
The output layer reads from this to build the final report.
"""

from datetime import datetime, timezone
from typing import Any


class SessionMemory:
    """
    Append-only log of every event in a war room session.
    Thread-safe for sequential (non-concurrent) use.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.finished_at: str | None = None
        self._events: list[dict] = []

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def log_tool_result(self, agent_name: str, tool_name: str, result: Any):
        self._append({
            "type": "tool_result",
            "agent": agent_name,
            "tool": tool_name,
            "result": self._safe_truncate(result),
        })

    def log_agent_report(self, report):
        self._append({
            "type": "agent_report",
            **report.to_dict(),
        })

    def log_debate(self, debate_result: dict):
        self._append({
            "type": "debate",
            **debate_result,
        })

    def log_orchestrator_note(self, note: str):
        self._append({
            "type": "orchestrator_note",
            "note": note,
        })

    def log_final_decision(self, decision: dict):
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self._append({
            "type": "final_decision",
            **decision,
        })

    def _append(self, event: dict):
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        event["seq"] = len(self._events) + 1
        self._events.append(event)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all_events(self) -> list[dict]:
        return list(self._events)

    def get_agent_reports(self) -> list[dict]:
        return [e for e in self._events if e["type"] == "agent_report"]

    def get_tool_results(self) -> list[dict]:
        return [e for e in self._events if e["type"] == "tool_result"]

    def get_debate(self) -> dict | None:
        debates = [e for e in self._events if e["type"] == "debate"]
        return debates[-1] if debates else None

    def get_final_decision(self) -> dict | None:
        decisions = [e for e in self._events if e["type"] == "final_decision"]
        return decisions[-1] if decisions else None

    def get_verdicts(self) -> list[dict]:
        """Return agent name + verdict + confidence for every agent report."""
        return [
            {
                "agent": e["agent_name"],
                "verdict": e["verdict"],
                "confidence": e["confidence"],
            }
            for e in self.get_agent_reports()
        ]

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total_events": len(self._events),
            "events": self._events,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_truncate(self, value: Any, max_chars: int = 800) -> Any:
        """Truncate large dicts/strings so session memory stays readable."""
        if isinstance(value, dict):
            text = str(value)
            return text[:max_chars] + "…" if len(text) > max_chars else value
        if isinstance(value, str) and len(value) > max_chars:
            return value[:max_chars] + "…"
        return value