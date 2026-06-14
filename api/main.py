"""
Sentinel AI — Investigation Gateway (FastAPI Backend)

Endpoints:
  GET  /                      → health check / system info
  GET  /health                → detailed health check
  POST /api/investigate        → run full investigation, return JSON report
  POST /api/investigate/stream → SSE stream of live agent reasoning
  GET  /api/agents             → list registered agents and their roles
  GET  /api/kb/stats            → knowledge base statistics

Run with:
  uvicorn api.main:app --reload --port 8000
"""

import json
import sys
import os
from pathlib import Path

# Ensure project root is on path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.config import FoundryConfig, get_logger
from core.orchestrator import investigate, investigate_stream
from agents.knowledge_agent import KB

logger = get_logger("API")

app = FastAPI(
    title="Sentinel AI — Multi-Agent Scam Investigation Network",
    description=(
        "A multi-agent reasoning system built on Microsoft Foundry that investigates "
        "suspicious messages, emails, and offers using specialized AI agents "
        "(Content, Pattern, Knowledge, Identity) coordinated by an Orchestrator "
        "and adjudicated by a Judge Agent."
    ),
    version="1.0.0",
)

# CORS — allow frontend (Next.js dev server + production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────
class InvestigateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Suspicious message text to analyze")
    content_type: str = Field(default="text", description="text | email | sms | whatsapp | url")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Congratulations! You won ₹50,000. Click here immediately to claim your reward.",
                "content_type": "sms",
            }
        }


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service": "Sentinel AI",
        "description": "Multi-Agent Scam Investigation Network",
        "track": "Microsoft Agents League Hackathon — Reasoning Agents",
        "status": "operational",
        "provider": FoundryConfig.get_active_provider(),
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "provider": FoundryConfig.get_active_provider(),
        "azure_configured": FoundryConfig.is_azure_configured(),
        "openai_configured": FoundryConfig.is_openai_configured(),
        "knowledge_base_campaigns": len(KB.get("campaigns", [])),
    }


@app.get("/api/agents")
async def list_agents():
    return {
        "orchestrator": "Coordinates all specialist agents in parallel and routes to Judge Agent",
        "agents": [
            {
                "id": "content_agent",
                "name": "Content Agent",
                "role": "Linguistic & psychological manipulation analysis",
                "signals": ["urgency", "emotional manipulation", "reward baiting", "threat language"],
            },
            {
                "id": "pattern_agent",
                "name": "Pattern Agent",
                "role": "Structural scam template & pattern matching",
                "signals": ["known scam templates", "suspicious URLs", "fraud structures"],
            },
            {
                "id": "knowledge_agent",
                "name": "Knowledge Agent",
                "role": "Threat intelligence & knowledge base retrieval (Foundry grounding)",
                "signals": ["known campaigns", "suspicious domains", "brand impersonation targets"],
            },
            {
                "id": "identity_agent",
                "name": "Identity Agent",
                "role": "Sender identity & authenticity verification",
                "signals": ["domain spoofing", "brand impersonation", "unofficial channels"],
            },
            {
                "id": "judge_agent",
                "name": "Judge Agent",
                "role": "Final arbiter — aggregates evidence, resolves disagreements, produces verdict",
                "signals": ["confidence-weighted aggregation", "multi-step reasoning", "recommendations"],
            },
        ],
    }


@app.get("/api/kb/stats")
async def kb_stats():
    return {
        "total_campaigns": len(KB.get("campaigns", [])),
        "campaigns": [
            {"id": c["id"], "name": c["name"], "threat_level": c["threat_level"]}
            for c in KB.get("campaigns", [])
        ],
        "suspicious_domains_tracked": len(KB.get("suspicious_domains", [])),
        "brand_targets_tracked": len(KB.get("brand_impersonation_targets", [])),
    }


@app.post("/api/investigate")
async def api_investigate(request: InvestigateRequest):
    """
    Run a full multi-agent investigation and return the complete report.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        report = await investigate(request.text)
        return report.to_dict()
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")


@app.post("/api/investigate/stream")
async def api_investigate_stream(request: InvestigateRequest):
    """
    Run a full multi-agent investigation, streaming live agent status
    via Server-Sent Events (SSE). Powers the "Live Agent Reasoning" UI screen.

    Event format: `data: <json>\\n\\n`
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    async def event_generator():
        async for event in investigate_stream(request.text):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable buffering on nginx/Azure
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
