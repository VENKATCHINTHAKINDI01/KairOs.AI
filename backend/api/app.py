"""
KairosAI — FastAPI Application
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.health  import router as health_router
from api.routes.warroom import router as warroom_router
from api.routes.monitor import router as monitor_router

app = FastAPI(
    title="KairosAI",
    description="Multi-agent product launch war room — powered by Groq",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins in dev so any Vite port works (5173, 5174, 5175, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(warroom_router)
app.include_router(monitor_router)


@app.get("/")
async def root():
    return {
        "name":    "KairosAI",
        "version": "1.0.0",
        "docs":    "/docs",
        "health":  "/health",
        "endpoints": {
            "run_war_room":  "POST /api/v1/warroom/run",
            "stream_live":   "WS   /api/v1/warroom/stream",
            "get_report":    "GET  /api/v1/warroom/report/{session_id}",
            "ask_monitor":   "POST /api/v1/monitor/ask",
            "list_sessions": "GET  /api/v1/warroom/sessions",
        },
    }