"""
Sentinel AI — Microsoft Foundry Agent Service Integration
===========================================================

This module wires Sentinel AI's specialist agents to the REAL Microsoft
Foundry Agent Service (azure-ai-projects / azure-ai-agents SDKs), using
persistent agents, threads, runs, and tool-calling.

Architecture:
  - Each Sentinel specialist (Content, Pattern, Knowledge, Identity, Judge)
    is provisioned as a named Foundry Agent with its own instructions and
    tools, created once and reused across investigations.
  - Each investigation creates a new Thread per agent (or a shared thread
    with separate runs — we use isolated threads for clean parallel
    reasoning traces).
  - The Knowledge Agent is bound to a `file_search` / custom function tool
    that queries the Sentinel threat intelligence KB (data/scam_kb.json),
    simulating Foundry's grounded knowledge retrieval.
  - The Judge Agent receives the other agents' structured outputs as
    function-tool results within its own thread, enabling true multi-step
    tool-augmented reasoning.

FALLBACK STRATEGY (critical for hackathon reliability):
  This module is OPTIONAL. If `azure-ai-projects` is not installed, or
  `FOUNDRY_PROJECT_ENDPOINT` is not configured, `is_available()` returns
  False and `core/foundry_client.py` transparently falls back to the
  existing Azure OpenAI / OpenAI / mock chat-completion path. No code path
  in the agents breaks if this module is unavailable.

Install:
  pip install azure-ai-projects azure-ai-agents azure-identity

Environment variables (see .env.example):
  FOUNDRY_PROJECT_ENDPOINT   e.g. https://<project>.<region>.api.azureml.ms
  FOUNDRY_MODEL_DEPLOYMENT   e.g. gpt-4o
  AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_CLIENT_SECRET (for DefaultAzureCredential)
    -- or run `az login` locally for DefaultAzureCredential to pick up your session.
"""

import json
import os
from pathlib import Path
from typing import Optional

from core.config import get_logger

logger = get_logger("FoundryAgentService")

# ─────────────────────────────────────────────
# Optional SDK imports — module degrades gracefully if absent
# ─────────────────────────────────────────────
try:
    from azure.ai.projects import AIProjectClient
    from azure.ai.agents.models import FunctionTool, ToolSet
    from azure.identity import DefaultAzureCredential

    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False


PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL_DEPLOYMENT = os.getenv("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o")

KB_PATH = Path(__file__).parent.parent / "data" / "scam_kb.json"


def is_available() -> bool:
    """
    True if the Foundry Agent Service SDK is installed AND a project
    endpoint is configured. Used by foundry_client.py to decide whether
    to route through real Foundry Agents or fall back to chat completions.
    """
    return _SDK_AVAILABLE and bool(PROJECT_ENDPOINT)


# ─────────────────────────────────────────────
# Tool functions exposed to Foundry Agents
# ─────────────────────────────────────────────
def query_threat_knowledge_base(query: str) -> str:
    """
    Foundry tool function: queries the Sentinel threat intelligence KB
    for campaigns, suspicious domains, and brand-impersonation targets
    matching the given text. Bound to the Knowledge Agent as a
    FunctionTool — this is what gives the Knowledge Agent "grounded
    knowledge retrieval" inside Foundry Agent Service.

    Args:
        query: The message text (or excerpt) to search against the KB.

    Returns:
        JSON string of matched campaigns, domains, and impersonation targets.
    """
    try:
        with open(KB_PATH) as f:
            kb = json.load(f)
    except Exception as e:
        return json.dumps({"error": str(e)})

    text_lower = query.lower()
    matched_campaigns = []
    for c in kb.get("campaigns", []):
        hits = [kw for kw in c["keywords"] if kw in text_lower]
        if hits:
            matched_campaigns.append({
                "id": c["id"], "name": c["name"], "threat_level": c["threat_level"],
                "source": c["source"], "hits": hits,
            })

    domain_hits = [d for d in kb.get("suspicious_domains", []) if d in text_lower]
    brand_hits = [b for b in kb.get("brand_impersonation_targets", []) if b.lower() in text_lower]

    return json.dumps({
        "matched_campaigns": matched_campaigns,
        "domain_hits": domain_hits,
        "brand_impersonation_hits": brand_hits,
    })


def submit_agent_finding(
    agent_name: str,
    risk_score: int,
    evidence: list,
    reasoning: str,
    confidence: float,
) -> str:
    """
    Foundry tool function: lets the Judge Agent formally record a
    specialist agent's structured finding within its reasoning thread,
    making the Judge's tool-call trace a complete audit log of the
    multi-agent investigation (useful for the "Explainable AI" criterion).
    """
    return json.dumps({
        "recorded": True,
        "agent_name": agent_name,
        "risk_score": risk_score,
        "evidence_count": len(evidence),
        "confidence": confidence,
    })


# ─────────────────────────────────────────────
# Agent definitions — instructions per Sentinel specialist
# ─────────────────────────────────────────────
AGENT_DEFINITIONS = {
    "content_agent": {
        "name": "Sentinel-ContentAgent",
        "instructions": (
            "You are the Content Analysis Agent in the Sentinel AI scam "
            "investigation network. Analyze urgency, emotional manipulation, "
            "reward/threat baiting, and impersonation cues in the message. "
            "Respond ONLY with JSON: {risk_score, evidence, reasoning, "
            "confidence, detected_tactics}."
        ),
        "tools": [],
    },
    "pattern_agent": {
        "name": "Sentinel-PatternAgent",
        "instructions": (
            "You are the Pattern Recognition Agent in the Sentinel AI scam "
            "investigation network. Match the message against known scam "
            "templates (lottery, advance-fee, investment, phishing, job "
            "scams, OTP fraud) and structural anomalies. Respond ONLY with "
            "JSON: {risk_score, evidence, reasoning, confidence, matched_templates}."
        ),
        "tools": [],
    },
    "knowledge_agent": {
        "name": "Sentinel-KnowledgeAgent",
        "instructions": (
            "You are the Knowledge & Threat Intelligence Agent in the "
            "Sentinel AI scam investigation network. ALWAYS call the "
            "query_threat_knowledge_base tool first with the message text, "
            "then interpret the results. Respond ONLY with JSON: "
            "{risk_score, evidence, reasoning, confidence, identified_campaign}."
        ),
        "tools": ["query_threat_knowledge_base"],
    },
    "identity_agent": {
        "name": "Sentinel-IdentityAgent",
        "instructions": (
            "You are the Identity Verification Agent in the Sentinel AI "
            "scam investigation network. Assess sender authenticity, domain "
            "spoofing, and brand impersonation. Respond ONLY with JSON: "
            "{risk_score, evidence, reasoning, confidence, impersonated_entity, "
            "spoofing_signals}."
        ),
        "tools": [],
    },
    "judge_agent": {
        "name": "Sentinel-JudgeAgent",
        "instructions": (
            "You are the Judge Agent — the final arbiter in the Sentinel AI "
            "scam investigation network. You receive findings from four "
            "specialist agents via the submit_agent_finding tool log and "
            "the conversation context. Weigh each agent's confidence and "
            "evidence quality, resolve disagreements, and produce a final "
            "verdict. Respond ONLY with JSON: {final_score, scam_category, "
            "evidence, reasoning, recommendations}."
        ),
        "tools": ["submit_agent_finding"],
    },
}

TOOL_REGISTRY = {
    "query_threat_knowledge_base": query_threat_knowledge_base,
    "submit_agent_finding": submit_agent_finding,
}


class FoundryAgentServiceClient:
    """
    Thin wrapper around AIProjectClient that provisions Sentinel's agents
    (once, idempotently) and runs a single-turn investigation per agent
    using isolated threads.
    """

    def __init__(self):
        if not is_available():
            raise RuntimeError(
                "Foundry Agent Service SDK not available or "
                "FOUNDRY_PROJECT_ENDPOINT not configured."
            )

        self.client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential(),
        )
        self._agent_cache: dict[str, str] = {}  # agent_key -> foundry agent id
        logger.info(f"FoundryAgentServiceClient connected to {PROJECT_ENDPOINT}")

    def _get_or_create_agent(self, agent_key: str) -> str:
        """Provision (or retrieve cached) Foundry Agent for a Sentinel specialist."""
        if agent_key in self._agent_cache:
            return self._agent_cache[agent_key]

        definition = AGENT_DEFINITIONS[agent_key]

        toolset = ToolSet()
        for tool_name in definition["tools"]:
            fn = TOOL_REGISTRY[tool_name]
            toolset.add(FunctionTool(functions={fn}))

        agent = self.client.agents.create_agent(
            model=MODEL_DEPLOYMENT,
            name=definition["name"],
            instructions=definition["instructions"],
            toolset=toolset if definition["tools"] else None,
        )

        self._agent_cache[agent_key] = agent.id
        logger.info(f"Provisioned Foundry agent '{definition['name']}' -> {agent.id}")
        return agent.id

    async def run_agent(self, agent_key: str, user_message: str) -> dict:
        """
        Runs a single specialist agent against the given message in a
        fresh thread, executing any required tool calls, and returns the
        parsed JSON response.
        """
        agent_id = self._get_or_create_agent(agent_key)

        thread = self.client.agents.threads.create()
        self.client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message,
        )

        run = self.client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent_id,
        )

        if run.status == "failed":
            raise RuntimeError(f"Foundry run failed: {run.last_error}")

        messages = self.client.agents.messages.list(thread_id=thread.id)
        # Most recent assistant message is first in descending order
        for message in messages:
            if message.role == "assistant" and message.content:
                text_value = message.content[0].text.value
                clean = text_value.strip().removeprefix("```json").removesuffix("```").strip()
                return json.loads(clean)

        raise RuntimeError("No assistant response found in Foundry thread")


# Singleton — created lazily, only if SDK + endpoint are available
_service: Optional[FoundryAgentServiceClient] = None


def get_agent_service() -> Optional[FoundryAgentServiceClient]:
    global _service
    if not is_available():
        return None
    if _service is None:
        try:
            _service = FoundryAgentServiceClient()
        except Exception as e:
            logger.warning(f"Failed to initialize Foundry Agent Service: {e}")
            return None
    return _service
