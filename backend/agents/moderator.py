"""
KairosAI — Debate Moderator Agent
------------------------------------
Runs structured challenge round after all agents submit reports.
Uses Groq (free) via OpenAI-compatible API.
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY", ""),
    base_url="https://api.groq.com/openai/v1",
)
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

MODERATOR_SYSTEM_PROMPT = """You are the Debate Moderator in a product launch war room.

Your job:
1. Review all agent reports and identify the biggest unresolved tension
2. Summarise each side's strongest argument in 1-2 sentences
3. Identify the specific evidence gap causing the split
4. Make a moderated ruling: which side has stronger evidence?
5. Output a resolved verdict for the orchestrator

Rules:
- Be fair and cite specific data from each agent's report
- If all agents agree, note the consensus clearly
- Never manufacture conflict that isn't there
- Your ruling must be grounded in data

Respond ONLY with valid JSON. No text before or after."""


class ModeratorAgent:
    name = "Debate Moderator"
    role = "Debate Moderator — resolves agent disagreements, surfaces consensus"

    def __init__(self):
        self._trace: list[str] = []

    def run(self, agent_reports: list) -> dict:
        self._log(f"\n{'─'*50}")
        self._log(f"[{self.name}] starting debate round...")

        # Summarise all reports
        summaries = []
        for r in agent_reports:
            rd = r.to_dict()
            summaries.append({
                "agent":        rd["agent_name"],
                "verdict":      rd["verdict"],
                "confidence":   rd["confidence"],
                "summary":      rd["summary"],
                "key_findings": rd["key_findings"][:3],
            })

        verdicts = [r["verdict"] for r in summaries]
        verdict_counts = {v: verdicts.count(v) for v in set(verdicts)}

        prompt = f"""All war room agents have submitted reports:

{json.dumps(summaries, indent=2)}

Verdict distribution: {json.dumps(verdict_counts)}

Run debate moderation and respond ONLY with this JSON:
{{
  "consensus_exists": true | false,
  "tension": "<1 sentence: what is the core disagreement?>",
  "side_a": {{
    "agents": ["<names>"],
    "verdict": "PROCEED|PAUSE|ROLL_BACK",
    "strongest_argument": "<1-2 sentence best case>"
  }},
  "side_b": {{
    "agents": ["<names>"],
    "verdict": "PROCEED|PAUSE|ROLL_BACK",
    "strongest_argument": "<1-2 sentence best case>"
  }},
  "evidence_gap": "<specific data point causing the split>",
  "ruling": "<1-2 sentence moderator ruling>",
  "resolved_verdict": "PROCEED" | "PAUSE" | "ROLL_BACK",
  "resolved_confidence": <integer 0-100>,
  "key_unresolved_question": "<one question still unanswered>"
}}"""

        self._log(f"  → calling Groq ({MODEL})...")
        t0 = time.time()
        response = _client.chat.completions.create(
            model=MODEL,
            max_tokens=1000,
            temperature=0.2,
            messages=[
                {"role": "system", "content": MODERATOR_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )
        elapsed = round((time.time() - t0) * 1000, 1)
        self._log(f"  ← Groq responded in {elapsed}ms")

        raw = response.choices[0].message.content.strip()

        # Extract JSON
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {
                "consensus_exists":        False,
                "tension":                 "Could not parse moderator response.",
                "resolved_verdict":        "PAUSE",
                "resolved_confidence":     50,
                "ruling":                  raw[:300],
                "key_unresolved_question": "Requires manual review.",
            }

        self._log(f"[{self.name}] resolved={result.get('resolved_verdict')} "
                  f"confidence={result.get('resolved_confidence')}")
        self._log(f"{'─'*50}")
        return result

    def _log(self, message: str):
        timestamp = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{timestamp}] {message}"
        self._trace.append(line)
        print(line)

    def get_trace(self) -> list[str]:
        return self._trace