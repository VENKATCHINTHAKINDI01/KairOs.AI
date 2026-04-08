"""
KairosAI — Health Routes
GET /health
GET /health/ready
"""

import os
from fastapi import APIRouter
from api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    )


@router.get("/health/ready")
async def ready():
    """
    Readiness check — verifies GROQ_API_KEY is set.
    Used by Docker/k8s to know when the container is ready.
    """
    key = os.getenv("GROQ_API_KEY", "")
    if not key or key == "your_groq_api_key_here":
        return {"status": "not_ready", "reason": "GROQ_API_KEY not configured"}
    return {"status": "ready"}