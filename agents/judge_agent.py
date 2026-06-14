"""
Sentinel AI — Judge Agent
Foundry Agent #5 (Final Arbiter): Evidence Aggregation & Verdict Generation

Responsibilities:
- Receive outputs from Content, Pattern, Knowledge, and Identity agents
- Resolve disagreements between agents (weighted reasoning)
- Aggregate all evidence into a coherent narrative
- Produce final risk score, verdict, confidence, and recommendations
- Categorize the scam type (if applicable)

This is the "Reasoning Agent" centerpiece for the hackathon —
it demonstrates multi-step reasoning over multiple agent outputs,
not just a simple average.
"""

import json
from core.config import (
    AgentResult, InvestigationReport, RiskLevel, Verdict,
    score_to_risk, score_to_verdict, score_to_confidence, get_logger
)
from core.foundry_client import get_foundry_client

logger = get_logger("JudgeAgent")

SYSTEM_PROMPT = """
You are the Judge Agent — the final arbiter in the Sentinel AI multi-agent scam
investigation network built on Microsoft Foundry.

You have received independent analyses from four specialist agents:
1. Content Agent       — linguistic & psychological manipulation analysis
2. Pattern Agent        — structural scam template matching
3. Knowledge Agent       — threat intelligence database lookups
4. Identity Agent        — sender authenticity & impersonation analysis

Your responsibilities:
1. WEIGH each agent's findings based on confidence and evidence quality.
   - Knowledge Agent findings (database-grounded) deserve extra weight when present.
   - Identity Agent findings (spoofing/impersonation) are strong scam signals.
   - Resolve disagreements: if one agent found strong grounded evidence (e.g. KB match)
     and another found weak/no evidence, lean toward the grounded finding but explain why.
2. AGGREGATE all unique evidence into a single coherent list.
3. CATEGORIZE the scam type if applicable (e.g. "Lottery Scam", "Phishing", "Job Scam",
   "Investment Fraud", "Government Impersonation", or null if not a scam).
4. PRODUCE a final risk score (0-100) that reflects your holistic judgment —
   this does NOT have to be a simple average; use reasoning.
5. WRITE a clear explanation of your reasoning process (multi-step, mention how you
   weighed each agent's input).
6. GENERATE 2-4 actionable recommendations for the user.

Respond ONLY with valid JSON:
{
  "final_score": <integer 0-100>,
  "scam_category": "<category or null>",
  "evidence": [<deduplicated, prioritized list of evidence strings, max 8>],
  "reasoning": "<multi-step reasoning narrative explaining how you weighed each agent>",
  "recommendations": [<2-4 specific actionable recommendations>]
}
"""


def _build_agent_summary(agent_results: list[AgentResult]) -> str:
    """Build a structured summary of all agent findings for the Judge's context."""
    summary = []
    for r in agent_results:
        summary.append({
            "agent":      r.agent_name,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level.value,
            "confidence": r.confidence,
            "evidence":   r.evidence,
            "reasoning":  r.reasoning,
            "metadata":   r.metadata,
        })
    return json.dumps(summary, indent=2)


def _fallback_aggregate(agent_results: list[AgentResult]) -> dict:
    """
    Deterministic fallback aggregation if LLM is unavailable.
    Uses confidence-weighted scoring with a bonus for multi-agent agreement.
    """
    if not agent_results:
        return {
            "final_score": 0,
            "scam_category": None,
            "evidence": [],
            "reasoning": "No agent results available.",
            "recommendations": ["Unable to analyze — please try again."],
        }

    # Confidence-weighted average
    total_weight = sum(r.confidence for r in agent_results) or 1.0
    weighted_score = sum(r.risk_score * r.confidence for r in agent_results) / total_weight

    # Agreement bonus: if multiple agents score >70, boost final score
    high_risk_count = sum(1 for r in agent_results if r.risk_score >= 70)
    if high_risk_count >= 3:
        weighted_score = min(98, weighted_score + 10)
    elif high_risk_count >= 2:
        weighted_score = min(98, weighted_score + 5)

    final_score = int(round(weighted_score))

    # Aggregate evidence
    all_evidence = []
    for r in agent_results:
        all_evidence.extend(r.evidence)
    deduped_evidence = list(dict.fromkeys(all_evidence))[:8]

    # Determine scam category from Knowledge/Pattern agent metadata
    scam_category = None
    for r in agent_results:
        if r.agent_name == "Knowledge Agent":
            scam_category = r.metadata.get("identified_campaign")
            if scam_category:
                break
        if r.agent_name == "Pattern Agent" and r.metadata.get("matched_templates"):
            scam_category = r.metadata["matched_templates"][0]

    # Recommendations based on score
    if final_score >= 80:
        recommendations = [
            "Do not click any links or respond to this message",
            "Block the sender immediately",
            "Report this message to cybercrime.gov.in or your bank's fraud helpline",
            "Do not share OTPs, passwords, or personal details with the sender",
        ]
    elif final_score >= 50:
        recommendations = [
            "Treat this message with caution and verify independently",
            "Contact the organization directly using official channels (not links in this message)",
            "Do not share sensitive information until verified",
        ]
    else:
        recommendations = [
            "Message appears low-risk, but remain cautious with personal information",
            "Verify sender identity if any action is requested",
        ]

    high_agents = [r.agent_name.replace(" Agent", "") for r in agent_results if r.risk_score >= 70]
    low_agents = [r.agent_name.replace(" Agent", "") for r in agent_results if r.risk_score < 40]

    if final_score >= 80:
        reasoning = (
            f"This message shows strong signs of a scam. "
            f"{', '.join(high_agents)} all found multiple red flags — "
            f"things like urgent threats, suspicious links, and a message "
            f"style that matches known scam campaigns. "
            f"When several independent checks agree this strongly, "
            f"it's a clear warning sign."
        )
    elif final_score >= 50:
        reasoning = (
            f"This message has some warning signs worth paying attention to. "
            f"{', '.join(high_agents) if high_agents else 'A few checks'} flagged "
            f"unusual patterns, though not every check agreed — so we'd call "
            f"this suspicious rather than a confirmed scam. Worth double-checking "
            f"before taking any action."
        )
    elif final_score >= 20:
        reasoning = (
            f"This message looks mostly normal, but a few small details stood "
            f"out enough to mention. Nothing here strongly suggests a scam, "
            f"but it's still good practice to verify before sharing personal "
            f"information."
        )
    else:
        reasoning = (
            f"This message doesn't show the patterns we typically associate "
            f"with scams — no urgent threats, suspicious links, or "
            f"impersonation signals were found. It looks safe."
        )

    return {
        "final_score": final_score,
        "scam_category": scam_category,
        "evidence": deduped_evidence,
        "reasoning": reasoning,
        "recommendations": recommendations,
    }


async def run(text: str, agent_results: list[AgentResult]) -> InvestigationReport:
    logger.info("Judge Agent aggregating evidence from all agents...")

    client = get_foundry_client()
    agent_summary = _build_agent_summary(agent_results)

    # In mock mode, the generic keyword-scanning mock isn't suited for
    # aggregation tasks (its input is a JSON dump of agent results, not
    # raw scam text). Use the purpose-built deterministic aggregator instead
    # — it produces high-quality, demo-ready output without an API key.
    if client.provider == "mock":
        fallback = _fallback_aggregate(agent_results)
        final_score     = fallback["final_score"]
        scam_category   = fallback["scam_category"]
        evidence        = fallback["evidence"]
        reasoning       = fallback["reasoning"]
        recommendations = fallback["recommendations"]

    else:
        try:
            result = await client.complete(
                system_prompt=SYSTEM_PROMPT,
                user_message=(
                    f"Original message under investigation:\n{text}\n\n"
                    f"Agent findings:\n{agent_summary}"
                ),
                agent_name="JudgeAgent",
                temperature=0.1,
                max_tokens=1000,
            )

            final_score     = max(0, min(100, int(result.get("final_score", 50))))
            scam_category   = result.get("scam_category")
            evidence        = result.get("evidence", [])
            reasoning       = result.get("reasoning", "")
            recommendations = result.get("recommendations", [])

            if not evidence:
                fallback = _fallback_aggregate(agent_results)
                evidence = fallback["evidence"]
            if not recommendations:
                fallback = _fallback_aggregate(agent_results)
                recommendations = fallback["recommendations"]

        except Exception as e:
            logger.error(f"Judge Agent LLM call failed, using fallback aggregation: {e}")
            fallback = _fallback_aggregate(agent_results)
            final_score     = fallback["final_score"]
            scam_category   = fallback["scam_category"]
            evidence        = fallback["evidence"]
            reasoning       = fallback["reasoning"]
            recommendations = fallback["recommendations"]

    report = InvestigationReport(
        input_text=text,
        final_score=final_score,
        verdict=score_to_verdict(final_score),
        risk_level=score_to_risk(final_score),
        confidence=score_to_confidence(final_score),
        evidence=evidence,
        recommendations=recommendations,
        agent_results=agent_results,
        reasoning=reasoning,
        scam_category=scam_category,
        provider_used=client.provider,
    )

    logger.info(
        f"Judge Agent verdict: {report.verdict.value} "
        f"(score={final_score}, category={scam_category})"
    )
    return report
