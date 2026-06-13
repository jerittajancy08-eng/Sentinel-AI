"use client";

import type { InvestigationReport } from "@/lib/types";
import RiskGauge from "./RiskGauge";

function verdictColor(verdict: string): string {
  switch (verdict) {
    case "SCAM":
      return "var(--risk-critical)";
    case "LIKELY SCAM":
      return "var(--risk-high)";
    case "SUSPICIOUS":
      return "var(--risk-medium)";
    case "LIKELY SAFE":
      return "var(--risk-low)";
    default:
      return "var(--risk-safe)";
  }
}

function scoreColor(score: number): string {
  if (score >= 85) return "var(--risk-critical)";
  if (score >= 65) return "var(--risk-high)";
  if (score >= 40) return "var(--risk-medium)";
  if (score >= 20) return "var(--risk-low)";
  return "var(--risk-safe)";
}

export default function VerdictReport({
  report,
}: {
  report: InvestigationReport;
}) {
  const color = verdictColor(report.verdict);

  return (
    <div className="animate-rise space-y-6">
      {/* Header card */}
      <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6 md:p-8">
        <div className="flex flex-col md:flex-row gap-6 md:gap-10 items-center md:items-start">
          <RiskGauge score={report.final_score} riskLevel={report.risk_level} />

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <span
                className="font-display text-2xl md:text-3xl font-bold tracking-tight"
                style={{ color }}
              >
                {report.verdict}
              </span>
              <span className="font-mono text-xs px-2 py-1 rounded border border-[var(--border)] text-[var(--text-secondary)]">
                Confidence: {report.confidence}
              </span>
              {report.scam_category && (
                <span className="font-mono text-xs px-2 py-1 rounded border border-[var(--border)] text-[var(--text-secondary)]">
                  {report.scam_category}
                </span>
              )}
            </div>

            <p className="mt-4 text-sm md:text-base text-[var(--text-secondary)] leading-relaxed">
              {report.reasoning}
            </p>

            {report.processing_ms !== null && (
              <p className="mt-3 font-mono text-xs text-[var(--text-muted)]">
                Investigation completed in {report.processing_ms}ms · provider:{" "}
                {report.provider_used}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Evidence + Recommendations grid */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6">
          <h3 className="font-display text-sm font-semibold tracking-wide text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: "var(--agent-cyan)" }}
            />
            EVIDENCE
          </h3>
          <ul className="space-y-2.5">
            {report.evidence.map((item, i) => (
              <li
                key={i}
                className="font-mono text-xs leading-relaxed text-[var(--text-secondary)] pl-4 border-l-2 border-[var(--border-soft)]"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6">
          <h3 className="font-display text-sm font-semibold tracking-wide text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: "var(--signal)" }}
            />
            RECOMMENDED ACTIONS
          </h3>
          <ul className="space-y-3">
            {report.recommendations.map((item, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-[var(--text-primary)]">
                <span className="font-mono text-xs mt-0.5 text-[var(--signal)]">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Per-agent breakdown */}
      <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6">
        <h3 className="font-display text-sm font-semibold tracking-wide text-[var(--text-primary)] mb-4">
          AGENT-BY-AGENT BREAKDOWN
        </h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {report.agent_results.map((agent) => (
            <details
              key={agent.agent_name}
              className="group rounded-[var(--radius-md)] border border-[var(--border-soft)] bg-[var(--surface-2)] p-4 [&_summary]:list-none"
            >
              <summary className="cursor-pointer">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-display text-sm font-semibold text-[var(--text-primary)]">
                    {agent.agent_name}
                  </span>
                  <span
                    className="font-mono text-sm font-bold"
                    style={{ color: scoreColor(agent.risk_score) }}
                  >
                    {agent.risk_score}
                  </span>
                </div>

                {/* Confidence bar */}
                <div className="mb-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-[10px] tracking-wider text-[var(--text-muted)]">
                      CONFIDENCE
                    </span>
                    <span className="font-mono text-[10px] text-[var(--text-secondary)]">
                      {Math.round(agent.confidence * 100)}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-[var(--border-soft)] overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.round(agent.confidence * 100)}%`,
                        backgroundColor: "var(--agent-cyan)",
                      }}
                    />
                  </div>
                </div>

                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  {agent.reasoning}
                </p>

                <span className="inline-block mt-2 font-mono text-[10px] tracking-wider text-[var(--agent-cyan)] group-open:hidden">
                  + SHOW EVIDENCE
                </span>
                <span className="hidden group-open:inline-block mt-2 font-mono text-[10px] tracking-wider text-[var(--agent-cyan)]">
                  − HIDE EVIDENCE
                </span>
              </summary>

              <ul className="mt-3 pt-3 border-t border-[var(--border-soft)] space-y-1.5">
                {agent.evidence.map((item, i) => (
                  <li
                    key={i}
                    className="font-mono text-[11px] leading-relaxed text-[var(--text-secondary)] pl-3 border-l-2 border-[var(--border-soft)]"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </div>
      </div>
    </div>
  );
}
