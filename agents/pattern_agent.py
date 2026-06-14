"""
Sentinel AI — Pattern Agent
Foundry Agent #2: Structural Pattern & Template Matching

Responsibilities:
- Known scam template matching (lottery, phishing, investment, job fraud)
- Message structure analysis
- URL and contact pattern detection
- Grammatical anomaly detection (common in translated scams)
- Number/monetary format anomalies
"""

import re
from core.config import AgentResult, RiskLevel, AgentStatus, score_to_risk, get_logger
from core.foundry_client import get_foundry_client

logger = get_logger("PatternAgent")

SYSTEM_PROMPT = """
You are the Pattern Recognition Agent in the Sentinel AI multi-agent system on Microsoft Foundry.

Your role: Match the message against known scam structural templates and fraud patterns.
Focus on:
1. Classic scam templates (Nigerian prince, lottery, advance-fee, romance, crypto)
2. Structural patterns (unexpected reward → verification request → fee demand)
3. Suspicious URLs, shortened links, unofficial domains
4. Phone number or contact patterns used in known fraud
5. Grammar/translation anomalies common in bulk scam messages
6. Unsolicited financial offers or unsolicited contact

Respond ONLY with valid JSON:
{
  "risk_score": <integer 0-100>,
  "evidence": [<specific pattern matches found>],
  "reasoning": "<one paragraph>",
  "confidence": <float 0.0-1.0>,
  "matched_templates": [<template names that match>]
}
"""

# ─── Local heuristic patterns (runs even in mock mode for speed) ─────────────
URL_PATTERN     = re.compile(r"https?://\S+|bit\.ly/\S+|tinyurl\.com/\S+|goo\.gl/\S+")
PHONE_PATTERN   = re.compile(r"(\+?91[\s-]?)?[6-9]\d{9}")
AMOUNT_PATTERN  = re.compile(r"₹\s*[\d,]+|rs\.?\s*[\d,]+|\d+\s*(lakh|crore|thousand)", re.IGNORECASE)
EMAIL_PATTERN   = re.compile(r"[\w.+-]+@[\w-]+\.(com|in|net|org|co\.in)")

SCAM_TEMPLATES = [
    ("Lottery / Prize Scam",       ["won", "winner", "prize", "congratulations", "selected", "chosen"]),
    ("Advance Fee Fraud",          ["registration fee", "processing fee", "advance fee", "transfer fee", "release fee"]),
    ("Investment / Crypto Scam",   ["guaranteed returns", "double your money", "profit", "invest now", "100%"]),
    ("Phishing Attack",            ["verify", "account suspended", "login", "click here", "secure your account"]),
    ("Government Impersonation",   ["income tax", "aadhaar", "pan card", "court summons", "police notice"]),
    ("Job / Work-From-Home Scam",  ["work from home", "earn daily", "part time", "registration fee", "hiring now"]),
    ("OTP / SIM Swap Fraud",       ["share otp", "otp", "one time password", "sim card", "mobile verification"]),
    ("Parcel / Delivery Scam",     ["package", "delivery failed", "customs fee", "parcel held", "pay to release"]),
    ("Romantic Relationship Scam", ["dear friend", "i am from", "i need your help", "god bless", "western union"]),
]


def _local_pattern_scan(text: str) -> tuple[int, list[str], list[str]]:
    """Fast local pattern scan — runs before (or instead of) LLM."""
    text_lower = text.lower()
    evidence   = []
    templates  = []
    score      = 0

    # URL check
    urls = URL_PATTERN.findall(text)
    if urls:
        evidence.append(f"Contains a shortened/suspicious link: {urls[0][:60]}")
        score += 20

    # Phone numbers
    phones = PHONE_PATTERN.findall(text)
    if phones:
        evidence.append(f"Includes a phone number ({phones[0]}) — common in scam messages")
        score += 8

    # Monetary amounts
    amount_match = AMOUNT_PATTERN.search(text)
    if amount_match:
        evidence.append(f"Mentions a money amount: {amount_match.group(0).strip()}")
        score += 10

    # Template matching
    for template_name, keywords in SCAM_TEMPLATES:
        hits = [kw for kw in keywords if kw in text_lower]
        if len(hits) >= 2:
            templates.append(template_name)
            evidence.append(f"Looks like a \u201c{template_name}\u201d — similar wording: {', '.join(hits[:3])}")
            score += 22
        elif len(hits) == 1:
            score += 6

    return min(score, 95), evidence, templates


async def run(text: str) -> AgentResult:
    logger.info("Pattern Agent starting analysis...")

    # Local pattern scan first (always runs, fast)
    local_score, local_evidence, matched_templates = _local_pattern_scan(text)

    # LLM deep analysis
    client = get_foundry_client()
    try:
        result = await client.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Analyze this message for structural scam patterns:\n\n{text}",
            agent_name="PatternAgent",
            temperature=0.1,
        )

        llm_score     = max(0, min(100, int(result.get("risk_score", local_score))))
        llm_evidence  = result.get("evidence", [])
        llm_reasoning = result.get("reasoning", "")
        confidence    = float(result.get("confidence", 0.6))
        llm_templates = result.get("matched_templates", [])

        # Merge and deduplicate
        final_score     = max(local_score, llm_score)
        final_evidence  = list(dict.fromkeys(local_evidence + llm_evidence))[:8]
        all_templates   = list(dict.fromkeys(matched_templates + llm_templates))

        if all_templates:
            reasoning = f"Matched {len(all_templates)} scam template(s): {', '.join(all_templates)}. {llm_reasoning}"
        else:
            reasoning = llm_reasoning or "No strong template matches found."

        agent_result = AgentResult(
            agent_name="Pattern Agent",
            risk_score=final_score,
            risk_level=score_to_risk(final_score),
            evidence=final_evidence,
            reasoning=reasoning,
            confidence=confidence,
            metadata={"matched_templates": all_templates, "provider": client.provider},
            status=AgentStatus.COMPLETED,
        )

        logger.info(f"Pattern Agent complete — score: {final_score}, templates: {all_templates}")
        return agent_result

    except Exception as e:
        logger.error(f"Pattern Agent failed: {e}")
        return AgentResult(
            agent_name="Pattern Agent",
            risk_score=local_score,
            risk_level=score_to_risk(local_score),
            evidence=local_evidence or ["Pattern analysis error"],
            reasoning=f"LLM analysis failed, using local scan results. Error: {e}",
            confidence=0.4,
            metadata={"matched_templates": matched_templates},
            status=AgentStatus.COMPLETED,
        )
