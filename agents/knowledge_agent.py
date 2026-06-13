"""
Sentinel AI — Knowledge Agent
Foundry Agent #3: Threat Intelligence & Knowledge Retrieval

Responsibilities:
- Query the Sentinel scam knowledge base (mimics Azure AI Search / Foundry knowledge retrieval)
- Match against known fraud campaigns
- Detect brand impersonation targets
- Identify known suspicious domains
- Cross-reference threat intelligence sources

In production: Uses Azure AI Search + Foundry knowledge retrieval.
In demo mode:  Uses in-memory vector-style matching against scam_kb.json.
"""

import json
import os
from pathlib import Path
from core.config import AgentResult, RiskLevel, AgentStatus, score_to_risk, get_logger
from core.foundry_client import get_foundry_client

logger = get_logger("KnowledgeAgent")

# ─── Load knowledge base ──────────────────────────────────────────────────────
KB_PATH = Path(__file__).parent.parent / "data" / "scam_kb.json"

def _load_kb() -> dict:
    try:
        with open(KB_PATH) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load knowledge base: {e}")
        return {"campaigns": [], "suspicious_domains": [], "brand_impersonation_targets": []}

KB = _load_kb()


# ─── Knowledge retrieval (Foundry AI Search simulation) ──────────────────────
def _query_knowledge_base(text: str) -> dict:
    """
    Simulates Microsoft Foundry / Azure AI Search vector retrieval.
    Matches text against the Sentinel scam knowledge base.
    Returns matched campaigns, domain hits, and impersonation targets.
    """
    text_lower = text.lower()
    matched_campaigns   = []
    domain_hits         = []
    impersonation_hits  = []
    score               = 0

    # Campaign matching
    for campaign in KB.get("campaigns", []):
        keyword_hits = [kw for kw in campaign["keywords"] if kw in text_lower]
        if keyword_hits:
            relevance = len(keyword_hits) / len(campaign["keywords"])
            if relevance >= 0.15:  # At least 15% keyword overlap
                matched_campaigns.append({
                    "id":          campaign["id"],
                    "name":        campaign["name"],
                    "threat_level": campaign["threat_level"],
                    "source":      campaign["source"],
                    "hits":        keyword_hits[:4],
                    "relevance":   round(relevance, 2),
                })
                level_score = {"CRITICAL": 35, "HIGH": 28, "MEDIUM": 18}.get(campaign["threat_level"], 10)
                score += level_score

    # Suspicious domain check
    for domain in KB.get("suspicious_domains", []):
        if domain in text_lower:
            domain_hits.append(domain)
            score += 25

    # Brand impersonation check
    for brand in KB.get("brand_impersonation_targets", []):
        if brand.lower() in text_lower:
            impersonation_hits.append(brand)
            score += 12

    return {
        "matched_campaigns":    matched_campaigns,
        "domain_hits":          domain_hits,
        "impersonation_hits":   impersonation_hits,
        "kb_score":             min(score, 98),
    }


SYSTEM_PROMPT = """
You are the Knowledge & Threat Intelligence Agent in the Sentinel AI system on Microsoft Foundry.

You have just retrieved relevant records from the Sentinel threat intelligence database.
Your role: Interpret the retrieved knowledge and produce a final threat assessment.

Focus on:
1. How well the message matches known scam campaigns
2. Confidence in campaign identification
3. Historical context (how widespread, how dangerous)
4. Source credibility of matches

Respond ONLY with valid JSON:
{
  "risk_score": <integer 0-100>,
  "evidence": [<evidence items grounded in KB matches>],
  "reasoning": "<one paragraph>",
  "confidence": <float 0.0-1.0>,
  "identified_campaign": "<campaign name or null>"
}
"""


async def run(text: str) -> AgentResult:
    logger.info("Knowledge Agent starting threat intelligence lookup...")

    # Step 1: Query knowledge base (Foundry knowledge retrieval simulation)
    kb_results = _query_knowledge_base(text)
    kb_score   = kb_results["kb_score"]

    logger.info(f"KB lookup complete — campaigns: {len(kb_results['matched_campaigns'])}, "
                f"domains: {len(kb_results['domain_hits'])}")

    # Build context for LLM
    kb_context = json.dumps(kb_results, indent=2)

    # Step 2: LLM reasoning over KB results
    client = get_foundry_client()
    try:
        result = await client.complete(
            system_prompt=SYSTEM_PROMPT,
            user_message=(
                f"Original message:\n{text}\n\n"
                f"Threat intelligence retrieval results:\n{kb_context}"
            ),
            agent_name="KnowledgeAgent",
            temperature=0.1,
        )

        llm_score  = max(0, min(100, int(result.get("risk_score", kb_score))))
        llm_evidence = result.get("evidence", [])
        reasoning  = result.get("reasoning", "")
        confidence = float(result.get("confidence", 0.65))
        campaign   = result.get("identified_campaign")

        # Build evidence from KB hits
        kb_evidence = []
        for c in kb_results["matched_campaigns"][:3]:
            kb_evidence.append(
                f"KB match: '{c['name']}' ({c['threat_level']}) — "
                f"triggers: {', '.join(c['hits'][:3])} [Source: {c['source']}]"
            )
        for d in kb_results["domain_hits"]:
            kb_evidence.append(f"Suspicious domain in blocklist: {d}")
        for b in kb_results["impersonation_hits"][:2]:
            kb_evidence.append(f"Brand impersonation detected: {b}")

        final_evidence = list(dict.fromkeys(kb_evidence + llm_evidence))[:8]
        final_score    = max(kb_score, llm_score)

        # Best campaign name
        if not campaign and kb_results["matched_campaigns"]:
            campaign = kb_results["matched_campaigns"][0]["name"]

        agent_result = AgentResult(
            agent_name="Knowledge Agent",
            risk_score=final_score,
            risk_level=score_to_risk(final_score),
            evidence=final_evidence,
            reasoning=reasoning or f"Matched {len(kb_results['matched_campaigns'])} known threat campaigns.",
            confidence=confidence,
            metadata={
                "matched_campaigns":   [c["name"] for c in kb_results["matched_campaigns"]],
                "domain_hits":         kb_results["domain_hits"],
                "impersonation_hits":  kb_results["impersonation_hits"],
                "identified_campaign": campaign,
                "provider":            client.provider,
            },
            status=AgentStatus.COMPLETED,
        )

        logger.info(f"Knowledge Agent complete — score: {final_score}, campaign: {campaign}")
        return agent_result

    except Exception as e:
        logger.error(f"Knowledge Agent failed: {e}")

        # Graceful fallback — return KB-only results
        kb_evidence = [
            f"KB: '{c['name']}' ({c['threat_level']})" for c in kb_results["matched_campaigns"][:4]
        ] or ["No matching threat campaigns found"]

        return AgentResult(
            agent_name="Knowledge Agent",
            risk_score=kb_score,
            risk_level=score_to_risk(kb_score),
            evidence=kb_evidence,
            reasoning=f"Threat intelligence scan only (LLM unavailable). KB matches: {len(kb_results['matched_campaigns'])}",
            confidence=0.5,
            metadata=kb_results,
            status=AgentStatus.COMPLETED,
        )
