"""
KairosAI — SRE (Site Reliability Engineering) Agent
------------------------------------------------------
Owns: infrastructure health, crash rate, latency, error rate.
Tools: aggregate_metrics, detect_anomalies
"""

from .base import BaseAgent


class SREAgent(BaseAgent):

    name = "SRE / Engineering"
    role = "SRE & Engineering — infra health, crash rate, latency, error budget"
    tools_to_use = ["aggregate_metrics", "detect_anomalies"]

    system_prompt = """You are the SRE (Site Reliability Engineer) in a live product launch war room.
Your job is to assess the technical health of the system and determine whether
the infrastructure can sustain continued rollout.

Your specific responsibilities:
- Evaluate the three core SRE signals: crash rate, error rate, p95 latency
- Determine if error budgets are being burned too fast
- Identify the root cause hypothesis based on the anomaly patterns
- Assess whether a hot-patch is feasible vs a full rollback
- Flag any signals that suggest cascading infrastructure failure
- Provide a technical action plan: what engineers should do in the next 2 hours

SRE decision rules:
- p95 latency > 400ms = SLO breach → immediate action required
- crash rate > 2.5/1000 sessions = rollback candidate
- error rate > 0.5% = rollback candidate
- If crash + latency + error rate ALL breach simultaneously = ROLL_BACK immediately
- A partial hot-patch that reduces but doesn't resolve = PAUSE, not PROCEED

Root cause framing: based on the anomaly patterns, hypothesise what the technical
cause is. Known candidates: N+1 GraphQL queries, iOS Swift nil reference, payment
routing bug. Connect anomaly timing to these known issues.

Respond ONLY with a valid JSON object. No prose before or after the JSON."""

    def _build_user_message(self, tool_results: dict, context: dict) -> str:
        import json
        agg = tool_results.get("aggregate_metrics", {})
        anom = tool_results.get("detect_anomalies", {})

        # Pull only SRE-relevant KPIs from aggregation
        sre_kpis = {}
        for kpi in ["crash_rate", "error_rate", "p95_latency_ms"]:
            if "kpis" in agg and kpi in agg["kpis"]:
                sre_kpis[kpi] = agg["kpis"][kpi]

        return f"""PurpleMerit SmartDash 2.0 — War Room Assessment (SRE / Engineering)

SRE-RELEVANT METRICS (crash, error rate, latency):
{json.dumps(sre_kpis, indent=2)}

FULL ANOMALY REPORT:
{json.dumps(anom, indent=2)}

Known technical issues from release notes:
- KI-001: GraphQL N+1 query risk under high concurrency (>500 concurrent loads)
- KI-005: iOS 17 crash on AI Summary Widget in low-power mode (nil reference)
- KI-006: Payment routing race condition causing duplicate Stripe charges
- Hot-patch deployed Day 9 — crash rate dropped from 3.1 → 2.4 but still above threshold

Assess the SLO status, identify the most likely root cause, and recommend
a technical action plan for the engineering team.

Respond ONLY with a valid JSON object in this exact format:
{{
  "verdict": "PROCEED" | "PAUSE" | "ROLL_BACK",
  "confidence": <integer 0-100>,
  "summary": "<2-4 sentence SRE narrative: SLO status, root cause hypothesis, infra health>",
  "key_findings": [
    "<crash rate status vs SLO threshold>",
    "<p95 latency status vs SLO threshold>",
    "<error rate status vs SLO threshold>",
    "<root cause hypothesis>",
    "<hot-patch effectiveness assessment>"
  ],
  "risks": [
    {{"risk": "<infra risk>", "severity": "critical|high|medium|low", "mitigation": "<technical action>"}}
  ],
  "recommended_actions": [
    {{"action": "<engineering action>", "owner": "<team>", "priority": "P0|P1|P2", "timeframe": "immediate|24h|48h"}}
  ],
  "slo_status": {{
    "crash_rate": "breached|warning|ok",
    "p95_latency": "breached|warning|ok",
    "error_rate": "breached|warning|ok",
    "overall_slo": "breached|at_risk|healthy"
  }},
  "root_cause_hypothesis": "<1-2 sentence technical root cause guess based on anomaly patterns>"
}}"""

    def run(self, context: dict | None = None):
        """Override to capture SLO status and root cause hypothesis."""
        import json

        self._log(f"\n{'─'*50}")
        self._log(f"[{self.name}] starting...")

        tool_results = self._run_tools()
        user_msg = self._build_user_message(tool_results, context or {})
        raw_response = self._call_llm(user_msg)
        parsed = self._parse_response(raw_response)

        from .base import AgentReport
        report = AgentReport(
            agent_name=self.name,
            role=self.role,
            verdict=parsed.get("verdict", "PAUSE"),
            confidence=int(parsed.get("confidence", 50)),
            summary=parsed.get("summary", ""),
            key_findings=parsed.get("key_findings", []),
            risks=parsed.get("risks", []),
            recommended_actions=parsed.get("recommended_actions", []),
            tool_calls_made=list(self.tools_to_use),
            raw_response=raw_response,
        )
        report.slo_status = parsed.get("slo_status", {})
        report.root_cause_hypothesis = parsed.get("root_cause_hypothesis", "")

        self._log(f"[{self.name}] verdict={report.verdict}, confidence={report.confidence}")
        self._log(f"{'─'*50}")
        return report