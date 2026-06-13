"""
Sentinel AI — Identity Agent
Foundry Agent #4: Sender Identity & Authenticity Analysis

Responsibilities:
- Sender/domain reputation analysis
- Brand impersonation detection
- Email header anomaly detection
- Phone number format fraud signals
- Social media / contact authenticity
- Spoofing indicators
"""

import re
from core.config import AgentResult, RiskLevel, AgentStatus, score_to_risk, get_logger
from core.foundry_client import get_foundry_client

logger = get_logger("IdentityAgent")

SYSTEM_PROMPT = """
You are the Identity Verification Agent in the Sentinel AI system on Microsoft Foundry.

Your role: Assess the authenticity of the sender/source identity in the message.
Focus on:
1. Domain spoofing signals (slight misspellings of legitimate brands)
2. Brand impersonation (claiming to be SBI, HDFC, PayTM, Google, Amazon, etc.)
3. Generic sender descriptions ("the management", "HR team", "bank official")
4. Inconsistencies between claimed identity and message content
5. Unofficial contact channels (personal WhatsApp number for "official" bank communication)
6. Missing or forged official identifiers (no employee ID, no official domain)

Respond ONLY with valid JSON:
{
  "risk_score": <integer 0-100>,
  "evidence": [<specific identity anomalies found>],
  "reasoning": "<one paragraph>",
  "confidence": <float 0.0-1.0>,
  "impersonated_entity": "<entity being impersonated or null>",
  "spoofing_signals": [<list of specific spoofing indicators>]
}
"""

# Known legitimate domains — if message references these but comes from elsewhere, flag it
BRAND_DOMAINS = {
    "sbi":             "sbi.co.in",
    "hdfc":            "hdfcbank.com",
    "icici":           "icicibank.com",
    "axis":            "axisbank.com",
    "paytm":           "paytm.com",
    "phonepe":         "phonepe.com",
    "google":          "google.com",
    "amazon":          "amazon.in",
    "flipkart":        "flipkart.com",
    "irctc":           "irctc.co.in",
    "income tax":      "incometax.gov.in",
    "aadhaar":         "uidai.gov.in",
    "uidai":           "uidai.gov.in",
    "rbi":             "rbi.org.in",
}

PERSONAL_CHANNEL_PATTERNS = [
    (re.compile(r"whatsapp", re.IGNORECASE),      "WhatsApp used for official communication"),
    (re.compile(r"telegram", re.IGNORECASE),       "Telegram used for official communication"),
    (re.compile(r"gmail\.com", re.IGNORECASE),     "Gmail address for official correspondence"),
    (re.compile(r"yahoo\.com", re.IGNORECASE),     "Yahoo address for official correspondence"),
    (re.compile(r"hotmail\.com", re.IGNORECASE),   "Hotmail address for official correspondence"),
    (re.compile(r"@\S+\.xyz", re.IGNORECASE),      "Suspicious TLD in email address (.xyz)"),
    (re.compile(r"@\S+\.online", re.IGNORECASE),   "Suspicious TLD in email address (.online)"),
    (re.compile(r"@\S+\.club", re.IGNORECASE),     "Suspicious TLD in email address (.club)"),
]

SPOOFED_DOMAIN_PATTERNS = [
    (re.compile(r"sbi-?bank|sbibank\.|sbionline", re.IGNORECASE),    "SBI domain spoofing"),
    (re.compile(r"hdfc-?bank|hdfcbankk", re.IGNORECASE),             "HDFC domain spoofing"),
    (re.compile(r"paytmlm|paytm-?official", re.IGNORECASE),           "PayTM domain spoofing"),
    (re.compile(r"amazon-?offer|amazn\.", re.IGNORECASE),             "Amazon domain spoofing"),
    (re.compile(r"income-?tax-?refund", re.IGNORECASE),               "Income Tax Dept spoofing"),
    (re.compile(r"gov\.in\.\w+|govt-?\w+\.online", re.IGNORECASE),   "Government domain spoofing"),
]

GENERIC_SENDER_PATTERNS = [
    r"dear (customer|user|friend|sir|madam|valued)",
    r"the (management|team|department|committee|board)",
    r"official (notice|alert|team)",
    r"helpdesk",
    r"support team",
    r"lottery (board|commission|committee)",
    r"prize (committee|board|department)",
]


def _local_identity_scan(text: str) -> tuple[int, list[str], list[str], str | None]:
    text_lower = text.lower()
    evidence   = []
    spoofing   = []
    score      = 0
    impersonated = None

    # Brand impersonation check
    for brand, legit_domain in BRAND_DOMAINS.items():
        if brand in text_lower:
            evidence.append(f"References '{brand.upper()}' — verify sender is from @{legit_domain}")
            impersonated = brand.upper()
            score += 15
            break

    # Spoofed domain patterns
    for pattern, label in SPOOFED_DOMAIN_PATTERNS:
        if pattern.search(text):
            spoofing.append(label)
            evidence.append(f"Domain spoofing detected: {label}")
            score += 30

    # Personal channel for official comms
    for pattern, label in PERSONAL_CHANNEL_PATTERNS:
        if pattern.search(text):
            evidence.append(f"Unofficial channel: {label}")
            score += 12

    # Generic sender language
    for p in GENERIC_SENDER_PATTERNS:
        if re.search(p, text_lower):
            label = p.split("(")[0].strip()
            evidence.append(f"Generic, non-specific sender language detected: '{label}'")
            score += 8
            break

    return min(score, 95), evidence, spoofing, impersonated


async def run(text: str) -> AgentResult:
    logger.info("Identity Agent starting sender verification...")

    local_score, local_evidence, spoofing_signals, impersonated = _local_identity_scan(text)

    client = get_foundry_client()
    try:
        result = await client.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Analyze sender identity authenticity in this message:\n\n{text}",
            agent_name="IdentityAgent",
            temperature=0.1,
        )

        llm_score         = max(0, min(100, int(result.get("risk_score", local_score))))
        llm_evidence      = result.get("evidence", [])
        reasoning         = result.get("reasoning", "")
        confidence        = float(result.get("confidence", 0.6))
        llm_spoofing      = result.get("spoofing_signals", [])
        llm_impersonated  = result.get("impersonated_entity")

        final_score    = max(local_score, llm_score)
        final_evidence = list(dict.fromkeys(local_evidence + llm_evidence))[:8]
        all_spoofing   = list(dict.fromkeys(spoofing_signals + llm_spoofing))
        entity         = llm_impersonated or impersonated

        agent_result = AgentResult(
            agent_name="Identity Agent",
            risk_score=final_score,
            risk_level=score_to_risk(final_score),
            evidence=final_evidence,
            reasoning=reasoning or "Sender identity analysis complete.",
            confidence=confidence,
            metadata={
                "impersonated_entity": entity,
                "spoofing_signals":    all_spoofing,
                "provider":            client.provider,
            },
            status=AgentStatus.COMPLETED,
        )

        logger.info(f"Identity Agent complete — score: {final_score}, impersonated: {entity}")
        return agent_result

    except Exception as e:
        logger.error(f"Identity Agent failed: {e}")
        return AgentResult(
            agent_name="Identity Agent",
            risk_score=local_score,
            risk_level=score_to_risk(local_score),
            evidence=local_evidence or ["Identity analysis error — defaulting to local scan"],
            reasoning=f"LLM unavailable, using local identity scan. Error: {e}",
            confidence=0.4,
            metadata={"impersonated_entity": impersonated, "spoofing_signals": spoofing_signals},
            status=AgentStatus.COMPLETED,
        )
