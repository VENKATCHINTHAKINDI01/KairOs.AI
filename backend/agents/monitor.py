"""
KairosAI — War Room Monitor Agent
------------------------------------
Watches every step, maintains session memory, answers live Q&A.
Uses Groq (free) via OpenAI-compatible API.
"""

import json
import os
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

MONITOR_SYSTEM_PROMPT = """You are the War Room Monitor — the scribe and live assistant for the KairosAI war room.
You have access to the complete session memory: every agent report, tool result, and debate exchange.

Your responsibilities:
1. Answer questions about what happened in the war room
2. Summarise what any specific agent said about any specific topic
3. Track the evolving consensus across agents
4. Flag contradictions between agents

Rules:
- Always cite which agent said what
- If you don't know, say so — never invent details
- Be concise: 3-6 sentences max, use bullet points when listing
"""


class MonitorAgent:
    name = "War Room Monitor"
    role = "Session Monitor — full war room awareness and live Q&A"

    def __init__(self):
        self._session_memory: list[dict] = []
        self._trace: list[str] = []
        self._verdict_tally: dict[str, int] = {"PROCEED": 0, "PAUSE": 0, "ROLL_BACK": 0}
        self._confidence_scores: list[dict] = []

    def ingest(self, agent_report) -> None:
        report_dict = agent_report.to_dict()
        self._session_memory.append(report_dict)
        verdict = report_dict.get("verdict", "PAUSE")
        if verdict in self._verdict_tally:
            self._verdict_tally[verdict] += 1
        self._confidence_scores.append({
            "agent":      report_dict["agent_name"],
            "verdict":    verdict,
            "confidence": report_dict["confidence"],
        })
        self._log(f"[Monitor] ingested: {report_dict['agent_name']} → {verdict}")

    def ingest_tool_result(self, tool_name: str, result: dict) -> None:
        self._session_memory.append({
            "type":           "tool_result",
            "tool":           tool_name,
            "result_summary": str(result)[:500],
        })

    def ingest_debate(self, debate_record: dict) -> None:
        self._session_memory.append({"type": "debate", **debate_record})

    def answer(self, question: str) -> str:
        self._log(f"[Monitor] answering: {question}")
        memory_dump = json.dumps(self._session_memory, indent=2)

        prompt = f"""Session memory:
{memory_dump}

Verdict tally: {json.dumps(self._verdict_tally)}
Confidence scores: {json.dumps(self._confidence_scores)}

Answer this question concisely:
{question}"""

        t0 = time.time()
        response = _client.chat.completions.create(
            model=MODEL,
            max_tokens=600,
            temperature=0.2,
            messages=[
                {"role": "system", "content": MONITOR_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )
        elapsed = round((time.time() - t0) * 1000, 1)
        self._log(f"[Monitor] answered in {elapsed}ms")
        return response.choices[0].message.content

    def get_verdict_tally(self) -> dict:
        return self._verdict_tally.copy()

    def get_confidence_scores(self) -> list[dict]:
        return self._confidence_scores.copy()

    def get_current_consensus(self) -> str:
        if not self._verdict_tally or sum(self._verdict_tally.values()) == 0:
            return "No verdicts yet"
        return max(self._verdict_tally, key=self._verdict_tally.get)

    def get_avg_confidence(self) -> float:
        if not self._confidence_scores:
            return 0.0
        return round(
            sum(s["confidence"] for s in self._confidence_scores) / len(self._confidence_scores), 1
        )

    def get_session_summary(self) -> dict:
        return {
            "agents_reported":  len([m for m in self._session_memory if "agent_name" in m]),
            "verdict_tally":    self._verdict_tally,
            "current_consensus": self.get_current_consensus(),
            "avg_confidence":   self.get_avg_confidence(),
            "confidence_by_agent": self._confidence_scores,
        }

    def _log(self, message: str):
        timestamp = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{timestamp}] {message}"
        self._trace.append(line)
        print(line)

    def get_trace(self) -> list[str]:
        return self._trace