"""
Sentinel AI — Core Configuration & Shared Models
Centralizes all config, data models, and logging for the multi-agent system.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ─────────────────────────────────────────────
# Foundry / Azure OpenAI Configuration
# ─────────────────────────────────────────────
class FoundryConfig:
    """
    Microsoft Foundry + Azure OpenAI endpoint configuration.
    Reads from environment variables for production safety.
    Falls back to a mock mode so the demo always works.
    """
    AZURE_OPENAI_ENDPOINT: str = os.getenv(
        "AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/"
    )
    AZURE_OPENAI_KEY: str = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv(
        "AZURE_OPENAI_DEPLOYMENT", "gpt-4o"
    )
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"

    # Foundry Agent Service project details
    FOUNDRY_PROJECT_NAME: str = os.getenv("FOUNDRY_PROJECT_NAME", "sentinel-ai")
    FOUNDRY_SUBSCRIPTION_ID: str = os.getenv("FOUNDRY_SUBSCRIPTION_ID", "")
    FOUNDRY_RESOURCE_GROUP: str = os.getenv("FOUNDRY_RESOURCE_GROUP", "")

    # Microsoft Foundry Agent Service (azure-ai-projects SDK) — highest priority provider
    FOUNDRY_PROJECT_ENDPOINT: str = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
    FOUNDRY_MODEL_DEPLOYMENT: str = os.getenv("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o")

    # Fallback: direct OpenAI key (for free-tier demo)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Mock mode — set to True to run without any API key (demo/offline)
    MOCK_MODE: bool = os.getenv("SENTINEL_MOCK_MODE", "false").lower() == "true"

    @classmethod
    def is_azure_configured(cls) -> bool:
        return bool(cls.AZURE_OPENAI_KEY and cls.AZURE_OPENAI_ENDPOINT)

    @classmethod
    def is_openai_configured(cls) -> bool:
        return bool(cls.OPENAI_API_KEY)

    @classmethod
    def get_active_provider(cls) -> str:
        if cls.is_azure_configured():
            return "azure_foundry"
        if cls.is_openai_configured():
            return "openai"
        return "mock"


# ─────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────
class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"
    SAFE     = "SAFE"


class Verdict(str, Enum):
    SCAM          = "SCAM"
    LIKELY_SCAM   = "LIKELY SCAM"
    SUSPICIOUS    = "SUSPICIOUS"
    LIKELY_SAFE   = "LIKELY SAFE"
    SAFE          = "SAFE"


class AgentStatus(str, Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    COMPLETED  = "completed"
    FAILED     = "failed"


# ─────────────────────────────────────────────
# Agent Result Models
# ─────────────────────────────────────────────
@dataclass
class AgentResult:
    agent_name:   str
    risk_score:   int               # 0–100
    risk_level:   RiskLevel
    evidence:     list[str]         = field(default_factory=list)
    reasoning:    str               = ""
    confidence:   float             = 0.0   # 0.0–1.0
    metadata:     dict              = field(default_factory=dict)
    status:       AgentStatus       = AgentStatus.COMPLETED
    error:        Optional[str]     = None

    def to_dict(self) -> dict:
        return {
            "agent_name":  self.agent_name,
            "risk_score":  self.risk_score,
            "risk_level":  self.risk_level.value,
            "evidence":    self.evidence,
            "reasoning":   self.reasoning,
            "confidence":  self.confidence,
            "metadata":    self.metadata,
            "status":      self.status.value,
            "error":       self.error,
        }


@dataclass
class InvestigationReport:
    """Final output produced by the Judge Agent."""
    input_text:       str
    final_score:      int
    verdict:          Verdict
    risk_level:       RiskLevel
    confidence:       str               # HIGH / MEDIUM / LOW
    evidence:         list[str]         = field(default_factory=list)
    recommendations:  list[str]         = field(default_factory=list)
    agent_results:    list[AgentResult] = field(default_factory=list)
    reasoning:        str               = ""
    scam_category:    Optional[str]     = None
    processing_ms:    Optional[int]     = None
    provider_used:    str               = "mock"

    def to_dict(self) -> dict:
        return {
            "input_text":      self.input_text[:200] + "..." if len(self.input_text) > 200 else self.input_text,
            "final_score":     self.final_score,
            "verdict":         self.verdict.value,
            "risk_level":      self.risk_level.value,
            "confidence":      self.confidence,
            "evidence":        self.evidence,
            "recommendations": self.recommendations,
            "reasoning":       self.reasoning,
            "scam_category":   self.scam_category,
            "processing_ms":   self.processing_ms,
            "provider_used":   self.provider_used,
            "agent_results":   [r.to_dict() for r in self.agent_results],
        }


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def score_to_risk(score: int) -> RiskLevel:
    if score >= 85: return RiskLevel.CRITICAL
    if score >= 65: return RiskLevel.HIGH
    if score >= 40: return RiskLevel.MEDIUM
    if score >= 20: return RiskLevel.LOW
    return RiskLevel.SAFE


def score_to_verdict(score: int) -> Verdict:
    if score >= 80: return Verdict.SCAM
    if score >= 60: return Verdict.LIKELY_SCAM
    if score >= 40: return Verdict.SUSPICIOUS
    if score >= 20: return Verdict.LIKELY_SAFE
    return Verdict.SAFE


def score_to_confidence(score: int) -> str:
    if score >= 80 or score <= 20: return "HIGH"
    if score >= 60 or score <= 40: return "MEDIUM"
    return "LOW"
