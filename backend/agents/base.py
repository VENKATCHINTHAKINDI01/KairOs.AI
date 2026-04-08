"""
KairosAI — Agent Base Class
-----------------------------
LLM backend: Groq (free, fast).
Groq exposes an OpenAI-compatible API — we use the openai SDK
pointed at Groq's endpoint.

Set GROQ_API_KEY in your .env file.
Get a free key at: console.groq.com

Model: llama-3.3-70b-versatile (free, 128k context, strong reasoning)
"""

import os
import json
import time
from typing import Any
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL        = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

from openai import OpenAI

_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
)


# ---------------------------------------------------------------------------
# AgentReport — structured output every agent must return
# ---------------------------------------------------------------------------
class AgentReport:
    def __init__(
        self,
        agent_name: str,
        role: str,
        verdict: str,                      # "PROCEED" | "PAUSE" | "ROLL_BACK"
        confidence: int,                   # 0-100
        summary: str,
        key_findings: list[str],
        risks: list[dict],
        recommended_actions: list[dict],
        tool_calls_made: list[str],
        raw_response: str = "",
    ):
        self.agent_name        = agent_name
        self.role              = role
        self.verdict           = verdict
        self.confidence        = confidence
        self.summary           = summary
        self.key_findings      = key_findings
        self.risks             = risks
        self.recommended_actions = recommended_actions
        self.tool_calls_made   = tool_calls_made
        self.raw_response      = raw_response
        self.timestamp         = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "agent_name":          self.agent_name,
            "role":                self.role,
            "verdict":             self.verdict,
            "confidence":          self.confidence,
            "summary":             self.summary,
            "key_findings":        self.key_findings,
            "risks":               self.risks,
            "recommended_actions": self.recommended_actions,
            "tool_calls_made":     self.tool_calls_made,
            "timestamp":           self.timestamp,
        }


# ---------------------------------------------------------------------------
# Base Agent
# ---------------------------------------------------------------------------
class BaseAgent:
    """
    Base class for all KairosAI war room agents.
    Uses Groq's OpenAI-compatible API (free tier).

    Subclasses must define:
        name          : str
        role          : str
        system_prompt : str
        tools_to_use  : list[str]
    """

    name: str          = "Base Agent"
    role: str          = "Generic"
    system_prompt: str = "You are a helpful assistant."
    tools_to_use: list[str] = []

    def __init__(self):
        self._tool_results: dict[str, Any] = {}
        self._trace: list[str] = []

    # ------------------------------------------------------------------
    # Tool dispatch
    # ------------------------------------------------------------------
    def _run_tools(self) -> dict[str, Any]:
        from tools.aggregate_metrics import aggregate_metrics
        from tools.detect_anomalies  import detect_anomalies
        from tools.sentiment_analyzer import sentiment_analyzer
        from tools.trend_compare     import trend_compare
        from tools.risk_scorer       import risk_scorer

        tool_map = {
            "aggregate_metrics":  aggregate_metrics,
            "detect_anomalies":   detect_anomalies,
            "sentiment_analyzer": sentiment_analyzer,
            "trend_compare":      trend_compare,
            "risk_scorer":        risk_scorer,
        }

        results = {}
        for tool_name in self.tools_to_use:
            if tool_name in tool_map:
                self._log(f"  → calling tool: {tool_name}()")
                t0 = time.time()
                results[tool_name] = tool_map[tool_name]()
                elapsed = round((time.time() - t0) * 1000, 1)
                self._log(f"  ← {tool_name} returned in {elapsed}ms")

        self._tool_results = results
        return results

    # ------------------------------------------------------------------
    # Groq API call (OpenAI-compatible)
    # ------------------------------------------------------------------
    def _call_llm(self, user_message: str) -> str:
        self._log(f"  → calling Groq ({MODEL})...")
        t0 = time.time()

        response = _client.chat.completions.create(
            model=MODEL,
            max_tokens=1500,
            temperature=0.3,       # low temp = consistent structured output
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user",   "content": user_message},
            ],
        )

        elapsed = round((time.time() - t0) * 1000, 1)
        self._log(f"  ← Groq responded in {elapsed}ms")
        return response.choices[0].message.content

    # ------------------------------------------------------------------
    # Parse JSON from LLM response
    # ------------------------------------------------------------------
    def _parse_response(self, raw: str) -> dict:
        import re as _re
        text = raw.strip()

        # Step 1: strip markdown fences
        if "```" in text:
            lines = text.split("\n")
            stripped = []
            inside = False
            for line in lines:
                if line.startswith("```"):
                    inside = not inside
                    continue
                stripped.append(line)
            text = "\n".join(stripped).strip()

        # Step 2: extract outermost JSON object
        s = text.find("{")
        e = text.rfind("}") + 1
        if s != -1 and e > s:
            text = text[s:e]

        # Step 3: try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Step 4: fix trailing commas and control chars
        cleaned = _re.sub(r",\s*([}\]])", r"\1", text)
        cleaned = _re.sub(r"[\x00-\x1f\x7f]", " ", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Step 5: retry Groq with simplified prompt
        self._log("  ⚠️  JSON parse failed — retrying with simplified prompt")
        try:
            retry = _client.chat.completions.create(
                model=MODEL,
                max_tokens=600,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": "Respond with ONLY a valid JSON object. No prose, no markdown."},
                    {"role": "user", "content": (
                        "Convert this analysis to JSON with keys: verdict (PROCEED/PAUSE/ROLL_BACK), "
                        "confidence (0-100), summary (string), key_findings (string array), "
                        "risks (array of {risk,severity,mitigation}), "
                        "recommended_actions (array of {action,owner,priority,timeframe}).\n\n"
                        f"Analysis:\n{raw[:800]}"
                    )},
                ],
            )
            rt = retry.choices[0].message.content.strip()
            rs = rt.find("{"); re_ = rt.rfind("}") + 1
            if rs != -1 and re_ > rs:
                return json.loads(rt[rs:re_])
        except Exception:
            pass

        # Final fallback
        self._log("  ⚠️  All parse strategies failed — using safe fallback")
        return {
            "verdict":             "PAUSE",
            "confidence":          50,
            "summary":             raw[:300],
            "key_findings":        ["Response parsing failed — manual review required."],
            "risks":               [],
            "recommended_actions": [],
        }

    def run(self, context: dict | None = None) -> AgentReport:
        self._log(f"\n{'─'*50}")
        self._log(f"[{self.name}] starting...")

        tool_results = self._run_tools()
        user_msg     = self._build_user_message(tool_results, context or {})
        raw_response = self._call_llm(user_msg)
        parsed       = self._parse_response(raw_response)

        report = AgentReport(
            agent_name           = self.name,
            role                 = self.role,
            verdict              = parsed.get("verdict", "PAUSE"),
            confidence           = int(parsed.get("confidence", 50)),
            summary              = parsed.get("summary", ""),
            key_findings         = parsed.get("key_findings", []),
            risks                = parsed.get("risks", []),
            recommended_actions  = parsed.get("recommended_actions", []),
            tool_calls_made      = list(self.tools_to_use),
            raw_response         = raw_response,
        )

        self._log(f"[{self.name}] verdict={report.verdict}, confidence={report.confidence}")
        self._log(f"{'─'*50}")
        return report

    # ------------------------------------------------------------------
    # Default user message builder — subclasses override this
    # ------------------------------------------------------------------
    def _build_user_message(self, tool_results: dict, context: dict) -> str:
        tool_summary    = json.dumps(tool_results, indent=2)
        context_summary = json.dumps(context, indent=2) if context else "{}"

        return f"""You are participating in a live product launch war room for PurpleMerit's SmartDash 2.0 feature.

Your role: {self.role}

Tool results:
{tool_summary}

Context from other agents:
{context_summary}

Respond ONLY with a valid JSON object in this exact format (no text before or after):
{{
  "verdict": "PROCEED" | "PAUSE" | "ROLL_BACK",
  "confidence": <integer 0-100>,
  "summary": "<2-4 sentence narrative>",
  "key_findings": ["<finding 1>", "<finding 2>", "<finding 3>"],
  "risks": [
    {{"risk": "<description>", "severity": "critical|high|medium|low", "mitigation": "<action>"}}
  ],
  "recommended_actions": [
    {{"action": "<what to do>", "owner": "<team>", "priority": "P0|P1|P2", "timeframe": "immediate|24h|48h"}}
  ]
}}"""

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _log(self, message: str):
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        line = f"[{timestamp}] {message}"
        self._trace.append(line)
        print(line)

    def get_trace(self) -> list[str]:
        return self._trace