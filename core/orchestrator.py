"""
Sentinel AI — Orchestrator Agent
The central coordination layer of the Foundry Agent Service.

Responsibilities:
- Receive investigation requests from the API gateway
- Dispatch the message to all specialist agents IN PARALLEL
- Stream live status updates (for the "Live Agent Reasoning" UI screen)
- Collect all agent results
- Hand off to the Judge Agent for final verdict
- Return the complete InvestigationReport

This module is the heart of the "multi-agent orchestration" story for the
Reasoning Agents track — it demonstrates parallel agent dispatch, async
coordination, and a clear reasoning pipeline.
"""

import asyncio
import time
from typing import AsyncGenerator, Optional
from core.config import AgentResult, InvestigationReport, AgentStatus, get_logger
from agents import content_agent, pattern_agent, knowledge_agent, identity_agent, judge_agent

logger = get_logger("Orchestrator")


# ─────────────────────────────────────────────
# Agent registry — easy to extend with new agents
# ─────────────────────────────────────────────
SPECIALIST_AGENTS = [
    ("content_agent",   content_agent),
    ("pattern_agent",   pattern_agent),
    ("knowledge_agent", knowledge_agent),
    ("identity_agent",  identity_agent),
]


async def investigate(text: str) -> InvestigationReport:
    """
    Run a full investigation synchronously (no streaming).
    Used by the simple REST endpoint.
    """
    start = time.perf_counter()
    logger.info(f"Orchestrator: starting investigation (input length={len(text)})")

    # Dispatch all specialist agents in parallel
    tasks = [agent_module.run(text) for _, agent_module in SPECIALIST_AGENTS]
    agent_results: list[AgentResult] = await asyncio.gather(*tasks)

    logger.info("Orchestrator: all specialist agents complete, dispatching to Judge Agent")

    # Judge Agent aggregates everything
    report = await judge_agent.run(text, agent_results)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    report.processing_ms = elapsed_ms

    logger.info(f"Orchestrator: investigation complete in {elapsed_ms}ms — verdict: {report.verdict.value}")
    return report


async def investigate_stream(text: str) -> AsyncGenerator[dict, None]:
    """
    Run a full investigation, yielding live status events as each agent
    completes. Designed for Server-Sent Events (SSE) to power the
    "Live Agent Reasoning" UI screen.

    Event types yielded:
      - {"event": "agent_started",   "agent": "<name>"}
      - {"event": "agent_completed", "agent": "<name>", "result": {...}}
      - {"event": "agent_failed",    "agent": "<name>", "error": "..."}
      - {"event": "judge_started"}
      - {"event": "investigation_complete", "report": {...}}
    """
    start = time.perf_counter()
    logger.info(f"Orchestrator: starting STREAMED investigation (input length={len(text)})")

    for agent_id, _ in SPECIALIST_AGENTS:
        yield {"event": "agent_started", "agent": agent_id}

    # Wrap each agent run so we can yield completion events as they finish,
    # tagging each result with its registry id for stable downstream ordering.
    async def run_and_tag(agent_id: str, agent_module):
        try:
            result = await agent_module.run(text)
            return agent_id, result
        except Exception as e:
            logger.error(f"Orchestrator: {agent_id} raised unexpected error: {e}")
            from core.config import RiskLevel
            return agent_id, AgentResult(
                agent_name=agent_id,
                risk_score=50,
                risk_level=RiskLevel.MEDIUM,
                evidence=["Agent execution error"],
                reasoning=str(e),
                confidence=0.3,
                status=AgentStatus.FAILED,
                error=str(e),
            )

    tasks = [
        asyncio.create_task(run_and_tag(agent_id, agent_module))
        for agent_id, agent_module in SPECIALIST_AGENTS
    ]

    tagged_results: list[tuple[str, AgentResult]] = []
    for completed in asyncio.as_completed(tasks):
        agent_id, result = await completed
        tagged_results.append((agent_id, result))

        if result.status == AgentStatus.FAILED:
            yield {"event": "agent_failed", "agent": agent_id, "error": result.error}
        else:
            yield {"event": "agent_completed", "agent": agent_id, "result": result.to_dict()}

    # Preserve registry order for the Judge Agent regardless of completion order
    order = {agent_id: i for i, (agent_id, _) in enumerate(SPECIALIST_AGENTS)}
    tagged_results.sort(key=lambda pair: order.get(pair[0], 99))
    agent_results: list[AgentResult] = [result for _, result in tagged_results]

    yield {"event": "judge_started"}

    report = await judge_agent.run(text, agent_results)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    report.processing_ms = elapsed_ms

    logger.info(f"Orchestrator: STREAMED investigation complete in {elapsed_ms}ms — verdict: {report.verdict.value}")

    yield {"event": "investigation_complete", "report": report.to_dict()}
