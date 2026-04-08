"""
KairosAI — Trace Logger
-------------------------
Rich console logging for the war room session.
Every agent step, tool call, and decision gets a formatted,
timestamped, color-coded log line.
"""

import json
from datetime import datetime
from pathlib import Path


# ANSI color codes (no external deps)
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"


VERDICT_COLORS = {
    "PROCEED":   C.GREEN,
    "PAUSE":     C.YELLOW,
    "ROLL_BACK": C.RED,
}

SEVERITY_COLORS = {
    "critical": C.RED,
    "high":     C.YELLOW,
    "medium":   C.CYAN,
    "low":      C.GRAY,
}


def _ts() -> str:
    return datetime.utcnow().strftime("%H:%M:%S")


def _verdict_badge(verdict: str) -> str:
    color = VERDICT_COLORS.get(verdict, C.WHITE)
    label = {"PROCEED": "PROCEED", "PAUSE": "PAUSE", "ROLL_BACK": "ROLL BACK"}.get(verdict, verdict)
    return f"{color}{C.BOLD}[ {label} ]{C.RESET}"


class TraceLogger:
    """
    Writes formatted logs to console and optionally to a .jsonl file.
    """

    def __init__(self, session_id: str, log_dir: str = "logs"):
        self.session_id = session_id
        self._lines: list[str] = []
        self._jsonl_events: list[dict] = []

        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        self._log_file = log_path / f"session_{session_id}.jsonl"

    # ------------------------------------------------------------------
    # Public logging methods
    # ------------------------------------------------------------------

    def session_start(self, product: str):
        self._divider("═", C.CYAN)
        self._print(f"{C.CYAN}{C.BOLD}  KairosAI WAR ROOM INITIATED{C.RESET}")
        self._print(f"  {C.BOLD}Product  :{C.RESET} {product}")
        self._print(f"  {C.BOLD}Session  :{C.RESET} {self.session_id}")
        self._print(f"  {C.BOLD}Started  :{C.RESET} {datetime.utcnow().isoformat()}Z")
        self._divider("═", C.CYAN)
        self._event("session_start", {"product": product, "session_id": self.session_id})

    def phase(self, number: int, title: str):
        self._print(f"\n{C.BOLD}{C.BLUE}  ── PHASE {number}: {title} ──{C.RESET}")
        self._event("phase", {"number": number, "title": title})

    def agent_start(self, agent_name: str, tools: list[str]):
        self._print(f"\n{C.BOLD}  [{_ts()}] {agent_name}{C.RESET}")
        self._print(f"  {C.GRAY}  tools → {', '.join(tools) if tools else 'none (session memory)'}{C.RESET}")
        self._event("agent_start", {"agent": agent_name, "tools": tools})

    def tool_call(self, agent_name: str, tool_name: str, elapsed_ms: float):
        self._print(f"  {C.GRAY}  [{_ts()}] → {tool_name}() … {elapsed_ms}ms{C.RESET}")
        self._event("tool_call", {"agent": agent_name, "tool": tool_name, "elapsed_ms": elapsed_ms})

    def agent_verdict(self, agent_name: str, verdict: str, confidence: int, summary: str):
        badge = _verdict_badge(verdict)
        self._print(f"  {C.BOLD}  verdict :{C.RESET} {badge}  confidence={C.BOLD}{confidence}/100{C.RESET}")
        self._print(f"  {C.DIM}  {summary[:120]}{'…' if len(summary) > 120 else ''}{C.RESET}")
        self._event("agent_verdict", {
            "agent": agent_name, "verdict": verdict,
            "confidence": confidence, "summary": summary,
        })

    def debate_start(self):
        self._print(f"\n{C.MAGENTA}{C.BOLD}  ── DEBATE ROUND ──{C.RESET}")
        self._event("debate_start", {})

    def debate_challenge(self, challenges: list[str]):
        self._print(f"  {C.MAGENTA}  Risk agent challenges:{C.RESET}")
        for c in challenges[:3]:
            self._print(f"  {C.MAGENTA}    ⚑ {c[:90]}{C.RESET}")
        self._event("debate_challenges", {"challenges": challenges})

    def debate_resolved(self, verdict: str, confidence: int, ruling: str):
        badge = _verdict_badge(verdict)
        self._print(f"  {C.BOLD}  Moderator ruling:{C.RESET} {badge}  confidence={confidence}")
        self._print(f"  {C.DIM}  {ruling[:120]}{C.RESET}")
        self._event("debate_resolved", {"verdict": verdict, "confidence": confidence, "ruling": ruling})

    def final_decision(self, verdict: str, confidence: int, score_breakdown: dict):
        self._divider("═", VERDICT_COLORS.get(verdict, C.WHITE))
        color = VERDICT_COLORS.get(verdict, C.WHITE)
        label = {"PROCEED": "✅  PROCEED", "PAUSE": "⏸  PAUSE", "ROLL_BACK": "🔴  ROLL BACK"}.get(verdict, verdict)
        self._print(f"\n  {color}{C.BOLD}FINAL DECISION : {label}{C.RESET}")
        self._print(f"  {C.BOLD}Confidence     :{C.RESET} {confidence}/100")
        self._print(f"  {C.BOLD}Tally          :{C.RESET} {score_breakdown.get('verdict_distribution', {})}")
        self._print(f"  {C.DIM}{score_breakdown.get('interpretation', '')}{C.RESET}")
        self._divider("═", VERDICT_COLORS.get(verdict, C.WHITE))
        self._event("final_decision", {"verdict": verdict, "confidence": confidence})

    def risk_register(self, risks: list[dict]):
        self._print(f"\n  {C.BOLD}Risk Register ({len(risks)} risks):{C.RESET}")
        for risk in risks[:5]:
            sev = risk.get("severity", "low")
            color = SEVERITY_COLORS.get(sev, C.GRAY)
            self._print(
                f"  {color}  [{sev.upper():8}]{C.RESET} "
                f"{risk.get('risk','')[:65]}"
            )
        self._event("risk_register", {"count": len(risks)})

    def action_plan(self, actions_by_window: dict):
        self._print(f"\n  {C.BOLD}Action Plan:{C.RESET}")
        for window, actions in actions_by_window.items():
            if actions:
                label = {"immediate": "Immediate", "within_24h": "Within 24h", "within_48h": "Within 48h"}.get(window, window)
                self._print(f"  {C.CYAN}  {label}:{C.RESET}")
                for a in actions[:3]:
                    self._print(f"    → [{a.get('owner','?'):20}] {a.get('action','')[:55]}")
        self._event("action_plan", {"total": sum(len(v) for v in actions_by_window.values())})

    def session_end(self, report_path: str):
        self._print(f"\n  {C.GREEN}Report saved → {report_path}{C.RESET}")
        self._print(f"  {C.GRAY}Session {self.session_id} complete.{C.RESET}\n")
        self._event("session_end", {"report_path": report_path})
        self._flush_jsonl()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _print(self, text: str):
        print(text)
        # Strip ANSI for file storage
        import re
        clean = re.sub(r"\033\[[0-9;]*m", "", text)
        self._lines.append(clean)

    def _divider(self, char: str = "─", color: str = C.GRAY):
        self._print(f"{color}{'  ' + char * 52}{C.RESET}")

    def _event(self, event_type: str, data: dict):
        self._jsonl_events.append({
            "ts": datetime.utcnow().isoformat(),
            "type": event_type,
            **data,
        })

    def _flush_jsonl(self):
        try:
            with open(self._log_file, "w") as f:
                for event in self._jsonl_events:
                    f.write(json.dumps(event) + "\n")
        except Exception as e:
            print(f"  [TraceLogger] Could not write log file: {e}")

    def get_plain_log(self) -> list[str]:
        return list(self._lines)