"""
KairosAI — Data Analyst Agent
-------------------------------
Owns: quantitative analysis, anomaly detection, trend confidence.
Tools: aggregate_metrics, detect_anomalies, trend_compare
"""

from .base import BaseAgent


class AnalystAgent(BaseAgent):

    name = "Data Analyst"
    role = "Data Analyst — quantitative metrics, anomaly detection, statistical confidence"
    tools_to_use = ["aggregate_metrics", "detect_anomalies", "trend_compare"]

    system_prompt = """You are the Data Analyst in a live product launch war room.
Your job is to be the objective voice of the data — no opinions, only evidence.

Your specific responsibilities:
- Report the exact numbers: what changed, by how much, starting when
- Identify statistically significant anomalies vs normal launch noise
- Assess trend direction: is it getting better or worse?
- Flag correlations (e.g. latency spike correlates with crash rate spike)
- Express a confidence level in your findings based on sample size and data quality
- Call out where data is ambiguous or insufficient

Rules:
- Never overstate — if the data is mixed, say so
- Always cite specific numbers and dates
- Separate signal from noise: a single bad day ≠ a trend
- Your verdict should reflect statistical confidence, not gut feel

Respond ONLY with a valid JSON object. No prose before or after the JSON."""

    def _build_user_message(self, tool_results: dict, context: dict) -> str:
        import json
        agg = tool_results.get("aggregate_metrics", {})
        anom = tool_results.get("detect_anomalies", {})
        trend = tool_results.get("trend_compare", {})

        return f"""PurpleMerit SmartDash 2.0 — War Room Assessment (Data Analyst)

METRIC AGGREGATION (post-launch window):
{json.dumps(agg, indent=2)}

ANOMALY DETECTION RESULTS:
{json.dumps(anom, indent=2)}

TREND COMPARISON (baseline vs post-launch):
{json.dumps(trend, indent=2)}

Analyse the above data as a rigorous data analyst. Focus on:
1. Which KPIs show statistically significant degradation (not just noise)?
2. When did anomalies start — correlate with launch date?
3. Are there any improving signals that suggest natural recovery?
4. What is your confidence level in the verdict, and what would increase it?

Respond ONLY with a valid JSON object in this exact format:
{{
  "verdict": "PROCEED" | "PAUSE" | "ROLL_BACK",
  "confidence": <integer 0-100>,
  "summary": "<2-4 sentence analyst narrative with specific numbers and dates>",
  "key_findings": [
    "<finding with specific metric value and date>",
    "<anomaly correlation finding>",
    "<trend direction finding>",
    "<confidence assessment>"
  ],
  "risks": [
    {{"risk": "<data-backed risk>", "severity": "critical|high|medium|low", "mitigation": "<action>"}}
  ],
  "recommended_actions": [
    {{"action": "<action>", "owner": "<team>", "priority": "P0|P1|P2", "timeframe": "immediate|24h|48h"}}
  ]
}}"""