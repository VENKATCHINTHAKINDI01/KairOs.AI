"""
KairosAI — Orchestrator
-------------------------
The central coordinator that runs the entire war room session:

  Phase 1 — Data Analyst runs first (sets the numeric foundation)
  Phase 2 — PM, Marketing, SRE run in parallel (each with their lens)
  Phase 3 — Risk agent runs last in round 1 (with context from Phase 2)
  Phase 4 — Debate round (Risk challenges, Moderator resolves)
  Phase 5 — Final decision synthesis → structured JSON output

The MonitorAgent watches every step and maintains session memory.
"""

import uuid
import json
from datetime import datetime

from agents.pm import PMAgent
from agents.analyst import AnalystAgent
from agents.marketing import MarketingAgent
from agents.risk import RiskAgent
from agents.sre import SREAgent
from agents.monitor import MonitorAgent
from core.debate_engine import run_debate
from core.confidence_scorer import compute_confidence
from core.session_memory import SessionMemory


class Orchestrator:

    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.memory = SessionMemory(self.session_id)
        self.monitor = MonitorAgent()
        self._all_reports = []

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> dict:
        """
        Execute the full war room session.
        Returns the final structured decision dict.
        """
        self._banner("KairosAI WAR ROOM — PurpleMerit SmartDash 2.0")
        self._log(f"Session ID : {self.session_id}")
        self._log(f"Started at : {datetime.utcnow().isoformat()}Z")
        self._log(f"Product    : PurpleMerit — SmartDash 2.0 feature launch\n")

        # ── Phase 1: Data Analyst ─────────────────────────────────────
        self._phase("PHASE 1 — Data Analyst (numeric foundation)")
        analyst_report = self._run_agent(AnalystAgent())

        # ── Phase 2: PM + Marketing + SRE (independent lenses) ────────
        self._phase("PHASE 2 — PM / Marketing / SRE (role-specific views)")

        # PM gets analyst context
        pm_context = {"analyst_verdict": analyst_report.verdict,
                      "analyst_summary": analyst_report.summary}
        pm_report = self._run_agent(PMAgent(), context=pm_context)

        marketing_report = self._run_agent(MarketingAgent())

        sre_report = self._run_agent(SREAgent())

        # ── Phase 3: Risk Agent (sees all phase 2 verdicts) ───────────
        self._phase("PHASE 3 — Risk / Critic (challenges all assumptions)")
        risk_context = {
            "analyst":   {"verdict": analyst_report.verdict,  "confidence": analyst_report.confidence,  "summary": analyst_report.summary},
            "pm":        {"verdict": pm_report.verdict,       "confidence": pm_report.confidence,       "summary": pm_report.summary},
            "marketing": {"verdict": marketing_report.verdict,"confidence": marketing_report.confidence,"summary": marketing_report.summary},
            "sre":       {"verdict": sre_report.verdict,      "confidence": sre_report.confidence,      "summary": sre_report.summary},
        }
        risk_report = self._run_agent(RiskAgent(), context=risk_context)

        # ── Phase 4: Debate Round ──────────────────────────────────────
        self._phase("PHASE 4 — Debate Round (Risk vs PM, Moderator resolves)")
        debate_result = run_debate(
            all_reports=self._all_reports,
            risk_report=risk_report,
            pm_report=pm_report,
            monitor=self.monitor,
        )
        self.memory.log_debate(debate_result)

        # ── Phase 5: Final Decision ────────────────────────────────────
        self._phase("PHASE 5 — Final Decision Synthesis")
        final_decision = self._synthesise(debate_result)

        self.memory.log_final_decision(final_decision)

        self._banner("WAR ROOM COMPLETE")
        self._print_decision_summary(final_decision)

        return final_decision

    # ------------------------------------------------------------------
    # Agent runner — wraps each agent, feeds monitor, logs memory
    # ------------------------------------------------------------------

    def _run_agent(self, agent, context: dict | None = None):
        report = agent.run(context=context)
        self._all_reports.append(report)
        self.monitor.ingest(report)
        self.memory.log_agent_report(report)
        return report

    # ------------------------------------------------------------------
    # Final decision synthesis
    # ------------------------------------------------------------------

    def _synthesise(self, debate_result: dict) -> dict:
        """
        Combine all agent reports + debate result into the final decision JSON.
        Uses the debate moderator's resolved verdict as the primary signal,
        weighted by the confidence scorer.
        """
        # Confidence scoring
        confidence_data = compute_confidence(self._all_reports, debate_result)

        # Determine final verdict:
        # Debate moderator's resolved verdict takes priority.
        # If the weighted confidence score is very low (<45), escalate to PAUSE.
        resolved_verdict = debate_result.get("resolved_verdict", "PAUSE")
        final_score = confidence_data["weighted_score"]

        if resolved_verdict == "PROCEED" and final_score < 45:
            resolved_verdict = "PAUSE"
            self._log("⚠️  Confidence too low to PROCEED — escalating to PAUSE.")

        # Merge risks from all agents (deduplicated by description prefix)
        all_risks = self._merge_risks()

        # Merge actions from all agents (sorted by priority)
        all_actions = self._merge_actions()

        # Monitor session summary
        monitor_summary = self.monitor.get_session_summary()

        # Build the final structured output
        decision = {
            "meta": {
                "session_id":   self.session_id,
                "product":      "PurpleMerit — SmartDash 2.0",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "agents_run":   [r.agent_name for r in self._all_reports],
            },
            "decision":   resolved_verdict,
            "rationale": {
                "primary_drivers": self._extract_primary_drivers(),
                "metric_references": self._extract_metric_refs(),
                "feedback_summary": self._extract_feedback_summary(),
                "debate_resolution": debate_result.get("ruling", ""),
            },
            "confidence": {
                "weighted_score":  final_score,
                "interpretation": confidence_data["interpretation"],
                "verdict_distribution": confidence_data["verdict_distribution"],
                "agreement_ratio": confidence_data["agreement_ratio"],
                "per_agent":      confidence_data["per_agent"],
                "boosters":       confidence_data["confidence_boosters"],
            },
            "risk_register": all_risks[:8],   # top 8 risks
            "action_plan": {
                "immediate": [a for a in all_actions if a.get("timeframe") == "immediate"],
                "within_24h": [a for a in all_actions if a.get("timeframe") == "24h"],
                "within_48h": [a for a in all_actions if a.get("timeframe") == "48h"],
            },
            "communication_plan": self._build_comms_plan(),
            "agent_verdicts": [
                {
                    "agent":      r.agent_name,
                    "verdict":    r.verdict,
                    "confidence": r.confidence,
                    "summary":    r.summary,
                }
                for r in self._all_reports
            ],
            "debate_summary": {
                "tension":            debate_result.get("tension", ""),
                "consensus_exists":   debate_result.get("consensus_exists", False),
                "resolved_verdict":   debate_result.get("resolved_verdict", ""),
                "resolved_confidence":debate_result.get("resolved_confidence", 0),
                "key_unresolved":     debate_result.get("key_unresolved_question", ""),
            },
            "session_stats": {
                "total_agents":       len(self._all_reports),
                "verdict_tally":      monitor_summary["verdict_tally"],
                "avg_confidence":     monitor_summary["avg_confidence"],
                "total_events":       self.memory.get_all_events().__len__(),
            },
        }

        return decision

    # ------------------------------------------------------------------
    # Helpers for synthesise()
    # ------------------------------------------------------------------

    def _extract_primary_drivers(self) -> list[str]:
        """Pull the top key finding from each agent."""
        drivers = []
        for r in self._all_reports:
            if r.key_findings:
                drivers.append(f"[{r.agent_name}] {r.key_findings[0]}")
        return drivers

    def _extract_metric_refs(self) -> list[str]:
        """Extract metric-specific findings from analyst and SRE."""
        refs = []
        for r in self._all_reports:
            if r.agent_name in ("Data Analyst", "SRE / Engineering"):
                refs.extend(r.key_findings[:2])
        return refs

    def _extract_feedback_summary(self) -> str:
        """Get the marketing agent's summary (feedback-focused)."""
        for r in self._all_reports:
            if r.agent_name == "Marketing / Comms":
                return r.summary
        return ""

    def _merge_risks(self) -> list[dict]:
        """Merge all agent risk lists, remove near-duplicates, sort by severity."""
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        seen_prefixes: set[str] = set()
        merged = []

        for r in self._all_reports:
            for risk in r.risks:
                # Deduplicate by first 40 chars of description
                key = risk.get("risk", "")[:40].lower()
                if key not in seen_prefixes:
                    seen_prefixes.add(key)
                    risk["source_agent"] = r.agent_name
                    merged.append(risk)

        merged.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        return merged

    def _merge_actions(self) -> list[dict]:
        """Merge all recommended actions, sort P0 → P1 → P2."""
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        seen: set[str] = set()
        merged = []

        for r in self._all_reports:
            for action in r.recommended_actions:
                key = action.get("action", "")[:40].lower()
                if key not in seen:
                    seen.add(key)
                    action["source_agent"] = r.agent_name
                    merged.append(action)

        merged.sort(key=lambda x: priority_order.get(x.get("priority", "P2"), 2))
        return merged

    def _build_comms_plan(self) -> dict:
        """Extract comms plan from Marketing agent if available."""
        for r in self._all_reports:
            if r.agent_name == "Marketing / Comms":
                plan = getattr(r, "communication_plan", {})
                if plan:
                    return plan
        # Fallback
        return {
            "internal_message": "War room in progress. Updates to follow.",
            "user_message":     "We are aware of some issues and are actively investigating.",
            "enterprise_message": "Our team is reaching out to affected enterprise accounts directly.",
        }

    # ------------------------------------------------------------------
    # Console helpers
    # ------------------------------------------------------------------

    def _banner(self, title: str):
        width = 56
        print(f"\n{'═' * width}")
        print(f"  {title}")
        print(f"{'═' * width}")

    def _phase(self, title: str):
        print(f"\n{'─' * 52}")
        print(f"  {title}")
        print(f"{'─' * 52}")

    def _log(self, message: str):
        print(f"  {message}")

    def _print_decision_summary(self, decision: dict):
        verdict = decision["decision"]
        score   = decision["confidence"]["weighted_score"]
        interp  = decision["confidence"]["interpretation"]

        verdict_display = {
            "PROCEED":   "✅  PROCEED",
            "PAUSE":     "⏸️   PAUSE",
            "ROLL_BACK": "🔴  ROLL BACK",
        }.get(verdict, verdict)

        print(f"\n  FINAL DECISION : {verdict_display}")
        print(f"  Confidence     : {score}/100 — {interp}")
        print(f"  Tally          : {decision['session_stats']['verdict_tally']}")
        print(f"\n  Top risks:")
        for risk in decision["risk_register"][:3]:
            sev = risk.get("severity", "?").upper()
            print(f"    [{sev}] {risk.get('risk', '')[:70]}")
        print(f"\n  Immediate actions:")
        for action in decision["action_plan"]["immediate"][:3]:
            print(f"    → [{action.get('owner','?')}] {action.get('action','')[:70]}")
        print()


# ------------------------------------------------------------------
# Core __init__.py
# ------------------------------------------------------------------