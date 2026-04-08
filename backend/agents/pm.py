"""
KairosAI — Product Manager Agent
----------------------------------
Owns: success criteria, user impact framing, go/no-go recommendation.
Tools: aggregate_metrics, trend_compare
"""

from .base import BaseAgent


class PMAgent(BaseAgent):

    name = "Product Manager"
    role = "Product Manager — success criteria, user impact, go/no-go framing"
    tools_to_use = ["aggregate_metrics", "trend_compare"]

    system_prompt = """You are the Product Manager in a live product launch war room.
Your job is to evaluate whether the launch meets the pre-defined success criteria and
assess the real-world user impact.

Your specific responsibilities:
- Compare current metrics against the success criteria thresholds
- Quantify user impact: how many users are affected, how severely
- Frame the go/no-go decision from a product and user perspective
- Be data-driven but also consider strategic context (marketing momentum, rollback cost)
- You are NOT responsible for infra details — focus on product outcomes

Success criteria for SmartDash 2.0 (must-have):
1. Crash rate must stay below 2.0 per 1000 sessions
2. p95 latency must stay below 300ms
3. Payment success rate must stay above 97%
4. D1 retention must not drop more than 5pp from baseline (baseline was ~61.8%)

The feature can only PROCEED if ALL 4 must-have criteria are met.
If 1-2 are breached → PAUSE for investigation.
If 3+ are breached OR a payment/data integrity issue exists → ROLL_BACK.

Respond ONLY with a valid JSON object. No prose before or after the JSON."""

    def _build_user_message(self, tool_results: dict, context: dict) -> str:
        import json
        agg = tool_results.get("aggregate_metrics", {})
        trend = tool_results.get("trend_compare", {})

        return f"""PurpleMerit SmartDash 2.0 — War Room Assessment (Product Manager)

METRIC AGGREGATION:
{json.dumps(agg, indent=2)}

TREND COMPARISON (baseline vs post-launch):
{json.dumps(trend, indent=2)}

Evaluate each of the 4 must-have success criteria against the data above.
Count how many are currently breached and apply the go/no-go decision rules.

Respond ONLY with a valid JSON object in this exact format:
{{
  "verdict": "PROCEED" | "PAUSE" | "ROLL_BACK",
  "confidence": <integer 0-100>,
  "summary": "<2-4 sentence PM narrative about success criteria status and user impact>",
  "key_findings": [
    "<criterion 1 status with metric value>",
    "<criterion 2 status with metric value>",
    "<criterion 3 status>",
    "<criterion 4 status>",
    "<overall user impact statement>"
  ],
  "risks": [
    {{"risk": "<risk>", "severity": "critical|high|medium|low", "mitigation": "<action>"}}
  ],
  "recommended_actions": [
    {{"action": "<action>", "owner": "<team>", "priority": "P0|P1|P2", "timeframe": "immediate|24h|48h"}}
  ]
}}"""