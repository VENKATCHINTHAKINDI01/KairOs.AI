"""
KairosAI — Marketing / Comms Agent
-------------------------------------
Owns: user perception, sentiment, communication plan.
Tools: sentiment_analyzer
"""

from .base import BaseAgent


class MarketingAgent(BaseAgent):

    name = "Marketing / Comms"
    role = "Marketing & Communications — user perception, sentiment, messaging strategy"
    tools_to_use = ["sentiment_analyzer"]

    system_prompt = """You are the Marketing & Communications lead in a live product launch war room.
Your job is to assess how users are perceiving the launch and what must be communicated.

Your specific responsibilities:
- Analyse the sentiment and feedback signals: what are users actually saying?
- Identify reputation risks: negative reviews, churn signals, viral complaints
- Flag enterprise/high-value account concerns separately (they matter more)
- Recommend internal and external communication actions
- Draft the key message for each audience (users, press, internal team)
- Assess how the launch is landing vs expectations

Rules:
- Negative viral feedback on Twitter is a P0 even if metrics look OK
- Enterprise customer complaints require immediate personal outreach
- Any churn signals from paying customers must be escalated
- Payment failure complaints damage trust more than pure UX bugs
- Your verdict should reflect reputational risk, not just data

Respond ONLY with a valid JSON object. No prose before or after the JSON."""

    def _build_user_message(self, tool_results: dict, context: dict) -> str:
        import json
        sent = tool_results.get("sentiment_analyzer", {})

        return f"""PurpleMerit SmartDash 2.0 — War Room Assessment (Marketing & Comms)

SENTIMENT ANALYSIS RESULTS:
{json.dumps(sent, indent=2)}

Assess the reputational and perception situation based on the above.
Focus on:
1. Overall sentiment health and what is driving negative feedback
2. Any enterprise or high-value customer concerns
3. Payment or trust-related complaints (highest severity)
4. Churn signals — are users leaving or threatening to leave?
5. What must be communicated right now, to whom, and in what tone?

Respond ONLY with a valid JSON object in this exact format:
{{
  "verdict": "PROCEED" | "PAUSE" | "ROLL_BACK",
  "confidence": <integer 0-100>,
  "summary": "<2-4 sentence narrative on perception, reputation risk, and comms priority>",
  "key_findings": [
    "<sentiment score and dominant theme>",
    "<top complaint cluster with count>",
    "<enterprise/high-value account finding>",
    "<churn signal finding>",
    "<reputational risk assessment>"
  ],
  "risks": [
    {{"risk": "<reputation/comms risk>", "severity": "critical|high|medium|low", "mitigation": "<comms action>"}}
  ],
  "recommended_actions": [
    {{"action": "<comms action>", "owner": "<team>", "priority": "P0|P1|P2", "timeframe": "immediate|24h|48h"}}
  ],
  "communication_plan": {{
    "internal_message": "<1-2 sentence update for the internal team>",
    "user_message": "<1-2 sentence public-facing status update>",
    "enterprise_message": "<1 sentence personalised note for enterprise accounts>"
  }}
}}"""

    def run(self, context: dict | None = None):
        """Override to capture communication_plan from parsed response."""
        import json

        self._log(f"\n{'─'*50}")
        self._log(f"[{self.name}] starting...")

        tool_results = self._run_tools()
        user_msg = self._build_user_message(tool_results, context or {})
        raw_response = self._call_llm(user_msg)
        parsed = self._parse_response(raw_response)

        # Store comms plan as extra field on the report
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
        # Attach the communication plan
        report.communication_plan = parsed.get("communication_plan", {})

        self._log(f"[{self.name}] verdict={report.verdict}, confidence={report.confidence}")
        self._log(f"{'─'*50}")
        return report