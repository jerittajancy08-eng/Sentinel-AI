export type RiskLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SAFE";

export type Verdict =
  | "SCAM"
  | "LIKELY SCAM"
  | "SUSPICIOUS"
  | "LIKELY SAFE"
  | "SAFE";

export type AgentStatus = "pending" | "running" | "completed" | "failed";

export interface AgentResult {
  agent_name: string;
  risk_score: number;
  risk_level: RiskLevel;
  evidence: string[];
  reasoning: string;
  confidence: number;
  metadata: Record<string, unknown>;
  status: AgentStatus;
  error: string | null;
}

export interface InvestigationReport {
  input_text: string;
  final_score: number;
  verdict: Verdict;
  risk_level: RiskLevel;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  evidence: string[];
  recommendations: string[];
  reasoning: string;
  scam_category: string | null;
  processing_ms: number | null;
  provider_used: string;
  agent_results: AgentResult[];
}

export const AGENT_IDS = [
  "content_agent",
  "pattern_agent",
  "knowledge_agent",
  "identity_agent",
] as const;

export type AgentId = (typeof AGENT_IDS)[number];

export const AGENT_LABELS: Record<AgentId, string> = {
  content_agent: "Content Agent",
  pattern_agent: "Pattern Agent",
  knowledge_agent: "Knowledge Agent",
  identity_agent: "Identity Agent",
};

export const AGENT_DESCRIPTIONS: Record<AgentId, string> = {
  content_agent: "Reads tone, urgency & manipulation tactics",
  pattern_agent: "Matches structure against known scam templates",
  knowledge_agent: "Queries Sentinel threat intelligence base",
  identity_agent: "Verifies sender authenticity & impersonation",
};

export interface StreamEvent {
  event:
    | "agent_started"
    | "agent_completed"
    | "agent_failed"
    | "judge_started"
    | "investigation_complete";
  agent?: AgentId;
  result?: AgentResult;
  error?: string;
  report?: InvestigationReport;
}

/**
 * Friendly, Foundry-branded labels for the backend's active provider.
 * Keeps the UI presentable regardless of which tier of the fallback
 * chain (Foundry Agent Service -> Azure OpenAI -> OpenAI -> mock) is
 * currently serving requests.
 */
export const PROVIDER_LABELS: Record<string, string> = {
  foundry_agent_service: "Microsoft Foundry Agent Service",
  azure_foundry: "Microsoft Foundry (Azure OpenAI)",
  openai: "Foundry-Compatible Reasoning Engine",
  mock: "Sentinel Reasoning Engine (Foundry-Ready)",
};

export function providerLabel(provider: string): string {
  return PROVIDER_LABELS[provider] ?? "Microsoft Foundry";
}

export interface KbStats {
  total_campaigns: number;
  campaigns: { id: string; name: string; threat_level: string }[];
  suspicious_domains_tracked: number;
  brand_targets_tracked: number;
}

