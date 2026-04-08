"""
KairosAI — War Room Routes
POST /api/v1/warroom/run          — run war room, return full decision JSON
GET  /api/v1/warroom/status/{id}  — get session status
GET  /api/v1/warroom/report/{id}  — get full report for a session
WS   /api/v1/warroom/stream       — stream live agent events over WebSocket
"""

import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from api.schemas import RunWarRoomRequest
from api.routes.monitor import register_monitor

router = APIRouter(prefix="/api/v1/warroom", tags=["warroom"])

# In-memory store for completed session decisions
_session_store: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# REST — synchronous run (blocks until complete, returns full decision)
# ---------------------------------------------------------------------------

@router.post("/run")
async def run_war_room(request: RunWarRoomRequest):
    """
    Run the full war room session synchronously.
    Returns the complete structured decision JSON.
    Takes ~2-3 minutes with Groq.
    For live streaming use WS /api/v1/warroom/stream instead.
    """
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    from core.orchestrator import Orchestrator
    from output.report_builder import build_report

    orch = Orchestrator()

    # Run in thread pool so we don't block the event loop
    loop = asyncio.get_event_loop()
    decision = await loop.run_in_executor(None, orch.run)

    # Write reports
    report_paths = await loop.run_in_executor(None, build_report, decision)
    decision["report_paths"] = report_paths

    # Register monitor for Q&A
    register_monitor(orch.session_id, orch.monitor)

    # Cache decision
    _session_store[orch.session_id] = decision

    # Answer monitor question if provided
    if request.monitor_question:
        answer = await loop.run_in_executor(
            None, orch.monitor.answer, request.monitor_question
        )
        decision["monitor_answer"] = {
            "question": request.monitor_question,
            "answer":   answer,
        }

    return decision


# ---------------------------------------------------------------------------
# REST — session status and report retrieval
# ---------------------------------------------------------------------------

@router.get("/status/{session_id}")
async def get_status(session_id: str):
    if session_id not in _session_store:
        raise HTTPException(404, detail=f"Session '{session_id}' not found.")
    d = _session_store[session_id]
    return {
        "session_id": session_id,
        "decision":   d.get("decision"),
        "confidence": d.get("confidence", {}).get("weighted_score"),
        "tally":      d.get("session_stats", {}).get("verdict_tally"),
        "completed":  True,
    }


@router.get("/report/{session_id}")
async def get_report(session_id: str):
    if session_id not in _session_store:
        raise HTTPException(404, detail=f"Session '{session_id}' not found.")
    return _session_store[session_id]


@router.get("/sessions")
async def list_sessions():
    return {
        "sessions": [
            {
                "session_id": sid,
                "decision":   d.get("decision"),
                "confidence": d.get("confidence", {}).get("weighted_score"),
                "generated":  d.get("meta", {}).get("generated_at"),
            }
            for sid, d in _session_store.items()
        ]
    }


# ---------------------------------------------------------------------------
# WebSocket — live streaming
# ---------------------------------------------------------------------------

class StreamingOrchestrator:
    """
    Wraps the Orchestrator and monkey-patches agent _log methods
    so every step is broadcast over WebSocket in real time.
    """

    def __init__(self, websocket: WebSocket):
        self.ws = websocket

    async def _send(self, event_type: str, data: dict):
        try:
            await self.ws.send_text(json.dumps({
                "type":      event_type,
                "data":      data,
                "timestamp": datetime.utcnow().isoformat(),
            }))
        except Exception:
            pass  # client disconnected

    async def run(self) -> dict:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        from core.orchestrator import Orchestrator
        from output.report_builder import build_report

        orch = Orchestrator()

        await self._send("session_start", {
            "session_id": orch.session_id,
            "product":    "PurpleMerit — SmartDash 2.0",
        })

        # ── Phase 1: Analyst ─────────────────────────────────────────
        await self._send("phase_start", {"number": 1, "title": "Data Analyst"})
        loop = asyncio.get_event_loop()

        from agents.analyst import AnalystAgent
        analyst = AnalystAgent()
        await self._send("agent_start", {
            "agent": analyst.name,
            "tools": analyst.tools_to_use,
        })
        analyst_report = await loop.run_in_executor(None, analyst.run)
        orch._all_reports.append(analyst_report)
        orch.monitor.ingest(analyst_report)
        orch.memory.log_agent_report(analyst_report)
        await self._send("agent_verdict", {
            "agent":      analyst_report.agent_name,
            "verdict":    analyst_report.verdict,
            "confidence": analyst_report.confidence,
            "summary":    analyst_report.summary,
        })

        # ── Phase 2: PM + Marketing + SRE ────────────────────────────
        await self._send("phase_start", {"number": 2, "title": "PM / Marketing / SRE"})

        from agents.pm        import PMAgent
        from agents.marketing import MarketingAgent
        from agents.sre       import SREAgent

        pm_ctx = {"analyst_verdict": analyst_report.verdict,
                  "analyst_summary": analyst_report.summary}

        for AgentClass, ctx in [
            (PMAgent,        pm_ctx),
            (MarketingAgent, {}),
            (SREAgent,       {}),
        ]:
            agent = AgentClass()
            await self._send("agent_start", {
                "agent": agent.name,
                "tools": agent.tools_to_use,
            })
            report = await loop.run_in_executor(None, agent.run, ctx)
            orch._all_reports.append(report)
            orch.monitor.ingest(report)
            orch.memory.log_agent_report(report)
            await self._send("agent_verdict", {
                "agent":      report.agent_name,
                "verdict":    report.verdict,
                "confidence": report.confidence,
                "summary":    report.summary,
            })

        # ── Phase 3: Risk ─────────────────────────────────────────────
        await self._send("phase_start", {"number": 3, "title": "Risk / Critic"})

        from agents.risk import RiskAgent
        risk_ctx = {
            r.agent_name: {"verdict": r.verdict, "confidence": r.confidence,
                           "summary": r.summary}
            for r in orch._all_reports
        }
        risk_agent = RiskAgent()
        await self._send("agent_start", {
            "agent": risk_agent.name,
            "tools": risk_agent.tools_to_use,
        })
        risk_report = await loop.run_in_executor(None, risk_agent.run, risk_ctx)
        orch._all_reports.append(risk_report)
        orch.monitor.ingest(risk_report)
        orch.memory.log_agent_report(risk_report)
        await self._send("agent_verdict", {
            "agent":      risk_report.agent_name,
            "verdict":    risk_report.verdict,
            "confidence": risk_report.confidence,
            "summary":    risk_report.summary,
        })

        # ── Phase 4: Debate ───────────────────────────────────────────
        await self._send("debate_start", {})
        pm_report = next((r for r in orch._all_reports
                         if r.agent_name == "Product Manager"), orch._all_reports[0])

        from core.debate_engine import run_debate
        debate = await loop.run_in_executor(
            None, run_debate,
            orch._all_reports, risk_report, pm_report, orch.monitor
        )
        orch.memory.log_debate(debate)
        await self._send("debate_resolved", {
            "resolved_verdict":    debate.get("resolved_verdict"),
            "resolved_confidence": debate.get("resolved_confidence"),
            "ruling":              debate.get("ruling"),
            "tension":             debate.get("tension"),
        })

        # ── Phase 5: Final decision ───────────────────────────────────
        await self._send("phase_start", {"number": 5, "title": "Final Decision"})
        decision = await loop.run_in_executor(None, orch._synthesise, debate)
        orch.memory.log_final_decision(decision)

        report_paths = await loop.run_in_executor(None, build_report, decision)
        decision["report_paths"] = report_paths

        register_monitor(orch.session_id, orch.monitor)
        _session_store[orch.session_id] = decision

        await self._send("final_decision", {
            "session_id": orch.session_id,
            "decision":   decision["decision"],
            "confidence": decision["confidence"]["weighted_score"],
            "tally":      decision["session_stats"]["verdict_tally"],
            "top_risks":  [r["risk"] for r in decision["risk_register"][:3]],
        })

        await self._send("complete", {
            "session_id":   orch.session_id,
            "report_paths": report_paths,
        })

        return decision


@router.websocket("/stream")
async def stream_war_room(websocket: WebSocket):
    """
    WebSocket endpoint — streams live war room events to the frontend.

    Event types emitted:
        session_start   — war room kicked off
        phase_start     — a new phase beginning
        agent_start     — an agent is starting (tools listed)
        agent_verdict   — agent finished, verdict + confidence
        debate_start    — debate round beginning
        debate_resolved — moderator ruling
        final_decision  — the final call
        complete        — session done, report paths included
        error           — something went wrong
    """
    await websocket.accept()
    runner = StreamingOrchestrator(websocket)

    try:
        await runner.run()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"message": str(e)},
                "timestamp": datetime.utcnow().isoformat(),
            }))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass