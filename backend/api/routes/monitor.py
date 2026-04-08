"""
KairosAI — Monitor Routes
POST /api/v1/monitor/ask
"""

from fastapi import APIRouter, HTTPException
from api.schemas import MonitorAskRequest, MonitorAnswerResponse

router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])

# In-memory store: session_id → MonitorAgent instance
# Populated by the warroom router after each run
_monitor_registry: dict = {}


def register_monitor(session_id: str, monitor) -> None:
    """Called by the war room runner to register the monitor for Q&A."""
    _monitor_registry[session_id] = monitor


@router.post("/ask", response_model=MonitorAnswerResponse)
async def ask_monitor(request: MonitorAskRequest):
    """
    Ask the War Room Monitor a natural language question
    about a completed session.

    Example:
        POST /api/v1/monitor/ask
        { "session_id": "abc12345", "question": "What did the Risk agent say?" }
    """
    monitor = _monitor_registry.get(request.session_id)
    if not monitor:
        raise HTTPException(
            status_code=404,
            detail=f"No active session found for session_id='{request.session_id}'. "
                   "Run a war room first via POST /api/v1/warroom/run",
        )

    answer = monitor.answer(request.question)
    return MonitorAnswerResponse(
        question=request.question,
        answer=answer,
        session_id=request.session_id,
    )


@router.get("/sessions")
async def list_sessions():
    """List all session IDs that have an active monitor."""
    return {"sessions": list(_monitor_registry.keys())}