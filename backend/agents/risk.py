"""
KairosAI — Risk / Critic Agent
--------------------------------
Owns: assumption challenges, risk register, worst-case framing.
Tools: risk_scorer, detect_anomalies
"""

from .base import BaseAgent


class RiskAgent(BaseAgent):

    name = "Risk / Critic"
    role = "Risk & Critic — assumption challenges, risk register, worst-case analysis"
    tools_to_use = ["risk_scorer", "detect_anomalies"]

    system_prompt = """You are the Risk & Critic agent in a live product launch war room.
Your job is to be the devil's advocate — challenge assumptions, find the holes,
and ensure the team isn't being overconfident.

Your specific responsibilities:
- Build a full risk register with severity and mitigation for each risk
- Challenge any optimistic assumptions the other agents might make
- Identify cascading failure scenarios (what happens if X gets worse?)
- Assess risks the data doesn't show yet but logically could happen
- Request additional evidence when claims aren't data-backed
- Evaluate the rollback risk as well — rolling back has its own dangers

Rules:
- You are biased toward caution — a false positive (pausing unnecessarily) is
  much cheaper than a false negative (proceeding into a catastrophic failure)
- Payment integrity issues are ALWAYS critical — charge twice = legal risk
- Data corruption is irreversible — treat with extreme caution
- Do not accept "it's recovering" unless you see 3+ consecutive improving days
- Your verdict should reflect worst-case defensible outcome

When challenged by other agents: if their evidence is stronger than yours, you
can update your verdict. But demand specific data, not assertions.

Respond ONLY with a valid JSON object. No prose before or after the JSON."""

    def _build_user_message(self, tool_results: dict, context: dict) -> str:
        import json
        risk = tool_results.get("risk_scorer", {})
        anom = tool_results.get("detect_anomalies", {})

        # Include other agents' verdicts if available in context
        other_verdicts = ""
        if context:
            other_verdicts = f"\nOther agents have submitted these verdicts:\n{json.dumps(context, indent=2)}\n"

        return f"""PurpleMerit SmartDash 2.0 — War Room Assessment (Risk & Critic)

RISK REGISTER (from risk_scorer tool):
{json.dumps(risk, indent=2)}

ANOMALY DETECTION (from detect_anomalies tool):
{json.dumps(anom, indent=2)}
{other_verdicts}

As the Risk & Critic agent:
1. Validate the risk register — are any risks understated?
2. Identify cascading scenarios: what happens if latency keeps rising?
3. Challenge the recovery narrative: is it real or too early to call?
4. Flag any risks NOT in the tool output that you can infer from the patterns
5. What specific evidence is MISSING that would change your verdict?

Respond ONLY with a valid JSON object in this exact format:
{{
  "verdict": "PROCEED" | "PAUSE" | "ROLL_BACK",
  "confidence": <integer 0-100>,
  "summary": "<2-4 sentence risk-focused narrative, worst-case framing>",
  "key_findings": [
    "<most critical risk with evidence>",
    "<assumption being challenged>",
    "<cascading scenario>",
    "<missing evidence that is needed>",
    "<rollback risk assessment>"
  ],
  "risks": [
    {{"risk": "<risk>", "severity": "critical|high|medium|low", "mitigation": "<specific action>"}}
  ],
  "recommended_actions": [
    {{"action": "<action>", "owner": "<team>", "priority": "P0|P1|P2", "timeframe": "immediate|24h|48h"}}
  ],
  "challenges_to_other_agents": [
    "<challenge or question directed at another agent's assumption>"
  ],
  "evidence_requests": [
    "<specific data or metric needed before verdict can change>"
  ]
}}"""

    def run(self, context: dict | None = None):
        """Override to capture challenges and evidence_requests."""
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
            verdict=parsed.get("verdict", "ROLL_BACK"),
            confidence=int(parsed.get("confidence", 50)),
            summary=parsed.get("summary", ""),
            key_findings=parsed.get("key_findings", []),
            risks=parsed.get("risks", []),
            recommended_actions=parsed.get("recommended_actions", []),
            tool_calls_made=list(self.tools_to_use),
            raw_response=raw_response,
        )
        report.challenges = parsed.get("challenges_to_other_agents", [])
        report.evidence_requests = parsed.get("evidence_requests", [])

        self._log(f"[{self.name}] verdict={report.verdict}, confidence={report.confidence}")
        self._log(f"{'─'*50}")
        return report