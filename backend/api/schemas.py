"""
KairosAI — API Schemas
------------------------
Pydantic models for all request/response types.
"""

from pydantic import BaseModel
from typing import Any


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class RunWarRoomRequest(BaseModel):
    monitor_question: str | None = None


class MonitorAskRequest(BaseModel):
    question: str
    session_id: str


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AgentVerdictResponse(BaseModel):
    agent: str
    verdict: str
    confidence: int
    summary: str


class RiskItem(BaseModel):
    risk: str
    severity: str
    mitigation: str
    owner: str | None = None
    source_agent: str | None = None


class ActionItem(BaseModel):
    action: str
    owner: str
    priority: str
    timeframe: str
    source_agent: str | None = None


class ConfidenceResponse(BaseModel):
    weighted_score: int
    interpretation: str
    verdict_distribution: dict[str, int]
    agreement_ratio: float
    boosters: list[str]


class CommunicationPlan(BaseModel):
    internal_message: str
    user_message: str
    enterprise_message: str


class WarRoomResponse(BaseModel):
    session_id: str
    decision: str
    confidence: ConfidenceResponse
    rationale: dict[str, Any]
    risk_register: list[RiskItem]
    action_plan: dict[str, list[ActionItem]]
    communication_plan: CommunicationPlan
    agent_verdicts: list[AgentVerdictResponse]
    debate_summary: dict[str, Any]
    session_stats: dict[str, Any]
    report_paths: dict[str, str]


class MonitorAnswerResponse(BaseModel):
    question: str
    answer: str
    session_id: str


class HealthResponse(BaseModel):
    status: str
    version: str
    groq_model: str


# ---------------------------------------------------------------------------
# WebSocket event models (serialised to JSON and sent over WS)
# ---------------------------------------------------------------------------

class WSEvent(BaseModel):
    type: str        # phase_start | agent_start | tool_call | agent_verdict
                     # debate_start | debate_resolved | final_decision | complete | error
    data: dict[str, Any]