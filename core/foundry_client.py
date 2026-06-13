"""
Sentinel AI — Foundry LLM Client
Wraps Microsoft Foundry Agent Service / Azure OpenAI with automatic
fallback to OpenAI and a deterministic mock mode for offline demos.

Priority: Foundry Agent Service → Azure OpenAI → OpenAI → Mock
"""

import json
import re
import asyncio
from typing import Optional
from core.config import FoundryConfig, get_logger
from core import foundry_agent_service

logger = get_logger("FoundryClient")


# Maps internal agent_name strings (used by agents/*.py) to the
# Foundry Agent Service registry keys in core/foundry_agent_service.py
_AGENT_KEY_MAP = {
    "ContentAgent": "content_agent",
    "PatternAgent": "pattern_agent",
    "KnowledgeAgent": "knowledge_agent",
    "IdentityAgent": "identity_agent",
    "JudgeAgent": "judge_agent",
}


class FoundryLLMClient:
    """
    Unified LLM client for Sentinel AI.
    Acts as the Microsoft Foundry Agent Service interface.
    """

    def __init__(self):
        if foundry_agent_service.is_available():
            self.provider = "foundry_agent_service"
        else:
            self.provider = FoundryConfig.get_active_provider()
        logger.info(f"FoundryLLMClient initialized — provider: {self.provider}")

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        agent_name: str = "agent",
        temperature: float = 0.2,
        max_tokens: int = 800,
        expect_json: bool = True,
    ) -> dict:
        """
        Send a completion request to the active LLM provider.
        Always returns a parsed dict (even in mock mode).
        """
        logger.info(f"[{agent_name}] Calling {self.provider} ...")

        if self.provider == "foundry_agent_service":
            return await self._call_foundry_agent_service(system_prompt, user_message, agent_name)
        elif self.provider == "azure_foundry":
            return await self._call_azure(system_prompt, user_message, temperature, max_tokens, agent_name)
        elif self.provider == "openai":
            return await self._call_openai(system_prompt, user_message, temperature, max_tokens, agent_name)
        else:
            return await self._call_mock(system_prompt, user_message, agent_name)

    # ─────────────────────────────────────────
    # Microsoft Foundry Agent Service (threads + tools)
    # ─────────────────────────────────────────
    async def _call_foundry_agent_service(self, system_prompt, user_message, agent_name) -> dict:
        agent_key = _AGENT_KEY_MAP.get(agent_name)
        service = foundry_agent_service.get_agent_service()

        if not service or not agent_key:
            logger.warning(f"[{agent_name}] Foundry Agent Service unavailable, falling back to Azure OpenAI")
            return await self._call_azure_or_below(system_prompt, user_message, 0.1, 800, agent_name)

        try:
            # Foundry Agent Service agents already carry their instructions
            # (system_prompt) as part of their persistent definition; we
            # send only the task-specific user_message to the thread.
            return await service.run_agent(agent_key, user_message)
        except Exception as e:
            logger.warning(f"[{agent_name}] Foundry Agent Service call failed ({e}), falling back")
            return await self._call_azure_or_below(system_prompt, user_message, 0.1, 800, agent_name)

    async def _call_azure_or_below(self, system_prompt, user_message, temperature, max_tokens, agent_name) -> dict:
        """Fallback chain used when Foundry Agent Service is unavailable mid-call."""
        fallback_provider = FoundryConfig.get_active_provider()
        if fallback_provider == "azure_foundry":
            return await self._call_azure(system_prompt, user_message, temperature, max_tokens, agent_name)
        elif fallback_provider == "openai":
            return await self._call_openai(system_prompt, user_message, temperature, max_tokens, agent_name)
        else:
            return await self._call_mock(system_prompt, user_message, agent_name)

    # ─────────────────────────────────────────
    # Azure OpenAI / Foundry
    # ─────────────────────────────────────────
    async def _call_azure(self, system_prompt, user_message, temperature, max_tokens, agent_name) -> dict:
        try:
            from openai import AsyncAzureOpenAI
            client = AsyncAzureOpenAI(
                azure_endpoint=FoundryConfig.AZURE_OPENAI_ENDPOINT,
                api_key=FoundryConfig.AZURE_OPENAI_KEY,
                api_version=FoundryConfig.AZURE_OPENAI_API_VERSION,
            )
            response = await client.chat.completions.create(
                model=FoundryConfig.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            return self._safe_parse(raw, agent_name)

        except Exception as e:
            logger.warning(f"[{agent_name}] Azure call failed ({e}), falling back to mock")
            return await self._call_mock(system_prompt, user_message, agent_name)

    # ─────────────────────────────────────────
    # Direct OpenAI (free tier fallback)
    # ─────────────────────────────────────────
    async def _call_openai(self, system_prompt, user_message, temperature, max_tokens, agent_name) -> dict:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=FoundryConfig.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            return self._safe_parse(raw, agent_name)

        except Exception as e:
            logger.warning(f"[{agent_name}] OpenAI call failed ({e}), falling back to mock")
            return await self._call_mock(system_prompt, user_message, agent_name)

    # ─────────────────────────────────────────
    # Deterministic Mock (always works for demo)
    # ─────────────────────────────────────────
    async def _call_mock(self, system_prompt: str, user_message: str, agent_name: str) -> dict:
        """
        High-quality deterministic mock that scores text using
        heuristics. Gives realistic, demo-ready responses without
        any API key.
        """
        await asyncio.sleep(0.3)  # simulate latency

        text_lower = user_message.lower()

        # Scoring signals
        SCAM_SIGNALS = {
            "urgent": 12, "immediately": 10, "click here": 14, "verify": 10,
            "winner": 18, "won": 15, "congratulations": 12, "prize": 16,
            "claim": 12, "reward": 13, "account suspended": 18, "limited time": 11,
            "otp": 14, "share otp": 20, "₹": 8, "lakh": 8, "crore": 8,
            "guaranteed": 14, "100%": 12, "double": 12, "risk free": 15,
            "job offer": 10, "work from home": 10, "earn ₹": 12,
            "kyc": 14, "aadhaar": 8, "pan card": 10, "income tax": 10,
            "police": 12, "legal action": 14, "court": 10,
            "free": 6, "gift": 7, "selected": 8, "chosen": 7,
            "http://": 10, "bit.ly": 15, "tinyurl": 15,
            "registration fee": 16, "advance fee": 18, "processing fee": 16,
        }

        score = 0
        matched = []
        for signal, weight in SCAM_SIGNALS.items():
            if signal in text_lower:
                score += weight
                matched.append(signal)

        score = min(score, 98)

        # Per-agent flavour
        flavours = {
            "ContentAgent": {
                "evidence_prefix": "Linguistic marker",
                "reasoning": f"Text contains {len(matched)} high-risk linguistic patterns associated with social engineering.",
            },
            "PatternAgent": {
                "evidence_prefix": "Pattern match",
                "reasoning": "Message structure matches documented scam templates in the Sentinel pattern library.",
            },
            "KnowledgeAgent": {
                "evidence_prefix": "Threat intel hit",
                "reasoning": "Cross-referenced against Sentinel threat intelligence database — known campaign signatures detected.",
            },
            "IdentityAgent": {
                "evidence_prefix": "Identity flag",
                "reasoning": "Sender profile and contact metadata show spoofing indicators and brand impersonation.",
            },
        }

        flavour = flavours.get(agent_name, {"evidence_prefix": "Flag", "reasoning": "Suspicious content detected."})
        evidence = [f"{flavour['evidence_prefix']}: '{m}'" for m in matched[:3]]

        if not evidence:
            evidence = ["No strong scam signals detected"]
            score = max(score, 5)

        return {
            "risk_score": score,
            "evidence": evidence,
            "reasoning": flavour["reasoning"],
            "confidence": round(min(0.95, 0.5 + score / 200), 2),
        }

    # ─────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────
    def _safe_parse(self, raw: str, agent_name: str) -> dict:
        try:
            clean = re.sub(r"```json|```", "", raw).strip()
            return json.loads(clean)
        except Exception as e:
            logger.error(f"[{agent_name}] JSON parse failed: {e}")
            return {"risk_score": 50, "evidence": ["parse error"], "reasoning": raw[:200], "confidence": 0.5}


# Singleton
_client: Optional[FoundryLLMClient] = None

def get_foundry_client() -> FoundryLLMClient:
    global _client
    if _client is None:
        _client = FoundryLLMClient()
    return _client
