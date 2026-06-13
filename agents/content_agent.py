"""
Sentinel AI — Content Agent
Foundry Agent #1: Linguistic & Psychological Analysis

Responsibilities:
- Urgency detection
- Emotional manipulation signals
- Scam keyword density
- Sentence structure analysis
- Reward/threat baiting
"""

from core.config import AgentResult, RiskLevel, AgentStatus, score_to_risk, get_logger
from core.foundry_client import get_foundry_client

logger = get_logger("ContentAgent")

SYSTEM_PROMPT = """
You are the Content Analysis Agent in the Sentinel AI multi-agent scam detection network,
built on Microsoft Foundry.

Your role: Analyze the psychological and linguistic properties of the submitted text.
Focus on:
1. Urgency language ("immediately", "limited time", "act now")
2. Emotional manipulation (fear, greed, excitement bait)
3. Reward/prize baiting patterns
4. Threat language (account suspension, legal action)
5. Impersonation cues (official-sounding but suspicious)
6. Unusual monetary references

Respond ONLY with valid JSON:
{
  "risk_score": <integer 0-100>,
  "evidence": [<list of specific evidence strings found in text>],
  "reasoning": "<one paragraph explaining your analysis>",
  "confidence": <float 0.0-1.0>,
  "detected_tactics": [<psychological manipulation tactics used>]
}

Be precise. Ground every evidence item in the actual text.
"""


async def run(text: str) -> AgentResult:
    logger.info("Content Agent starting analysis...")

    client = get_foundry_client()

    try:
        result = await client.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Analyze this message for scam indicators:\n\n{text}",
            agent_name="ContentAgent",
            temperature=0.1,
        )

        score      = max(0, min(100, int(result.get("risk_score", 50))))
        evidence   = result.get("evidence", [])
        reasoning  = result.get("reasoning", "")
        confidence = float(result.get("confidence", 0.5))
        tactics    = result.get("detected_tactics", [])

        if tactics:
            evidence = evidence + [f"Tactic: {t}" for t in tactics[:2]]

        agent_result = AgentResult(
            agent_name="Content Agent",
            risk_score=score,
            risk_level=score_to_risk(score),
            evidence=evidence,
            reasoning=reasoning,
            confidence=confidence,
            metadata={"tactics": tactics, "provider": client.provider},
            status=AgentStatus.COMPLETED,
        )

        logger.info(f"Content Agent complete — score: {score}, evidence items: {len(evidence)}")
        return agent_result

    except Exception as e:
        logger.error(f"Content Agent failed: {e}")
        return AgentResult(
            agent_name="Content Agent",
            risk_score=50,
            risk_level=RiskLevel.MEDIUM,
            evidence=["Analysis error — defaulting to medium risk"],
            reasoning=str(e),
            confidence=0.3,
            status=AgentStatus.FAILED,
            error=str(e),
        )
