"use client";

import type { InvestigationReport } from "@/lib/types";
import { CONFIDENCE_LABELS, VERDICT_LABELS, providerLabel } from "@/lib/types";
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
  const verdictText = VERDICT_LABELS[report.verdict] ?? report.verdict;
  const confidenceText = CONFIDENCE_LABELS[report.confidence] ?? report.confidence;

  return (
    <div className="animate-rise space-y-6">
      {/* Header card */}
      <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6 md:p-8">
        <div className="flex flex-col md:flex-row gap-6 md:gap-10 items-center md:items-start">
          <RiskGauge score={report.final_score} riskLevel={report.risk_level} />

          <div className="flex-1 min-w-0 text-center md:text-left">
            <h3
              className="font-display text-2xl md:text-3xl font-bold tracking-tight text-balance"
              style={{ color }}
            >
              {verdictText}
            </h3>

            {report.scam_category && (
              <p className="mt-1 text-sm text-[var(--text-secondary)]">
                Looks similar to a known scam type:{" "}
                <span className="text-[var(--text-primary)] font-medium">
                  {report.scam_category}
                </span>
              </p>
            )}

            <p className="mt-4 text-sm md:text-base text-[var(--text-primary)] leading-relaxed">
              {report.reasoning}
            </p>

            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              {confidenceText}.
            </p>
          </div>
        </div>
      </div>

      {/* Evidence + Recommendations grid */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6">
          <h3 className="font-display text-base font-semibold text-[var(--text-primary)] mb-1">
            Why we think this
          </h3>
          <p className="text-xs text-[var(--text-secondary)] mb-4">
            Here&apos;s what stood out in the message
          </p>
          <ul className="space-y-2.5">
            {report.evidence.map((item, i) => (
              <li
                key={i}
                className="text-sm leading-relaxed text-[var(--text-secondary)] pl-4 border-l-2 border-[var(--border-soft)]"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6">
          <h3 className="font-display text-base font-semibold text-[var(--text-primary)] mb-1">
            What you should do
          </h3>
          <p className="text-xs text-[var(--text-secondary)] mb-4">
            Recommended next steps
          </p>
          <ul className="space-y-3">
            {report.recommendations.map((item, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-[var(--text-primary)]">
                <span
                  className="flex items-center justify-center w-5 h-5 rounded-full text-xs font-semibold shrink-0 mt-0.5"
                  style={{ backgroundColor: "var(--signal-glow)", color: "var(--signal)" }}
                >
                  {i + 1}
                </span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Per-agent breakdown */}
      <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-6">
        <h3 className="font-display text-base font-semibold text-[var(--text-primary)] mb-1">
          How each agent checked this
        </h3>
        <p className="text-xs text-[var(--text-secondary)] mb-4">
          Tap a card to see exactly what each agent found
        </p>
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
                    className="font-display text-sm font-bold"
                    style={{ color: scoreColor(agent.risk_score) }}
                  >
                    {agent.risk_score}/100
                  </span>
                </div>

                {/* Confidence bar */}
                <div className="mb-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-[var(--text-muted)]">
                      How sure
                    </span>
                    <span className="text-[11px] text-[var(--text-secondary)]">
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

                <span className="inline-block mt-2 text-xs font-medium text-[var(--agent-cyan)] group-open:hidden">
                  Show details
                </span>
                <span className="hidden group-open:inline-block mt-2 text-xs font-medium text-[var(--agent-cyan)]">
                  Hide details
                </span>
              </summary>

              <ul className="mt-3 pt-3 border-t border-[var(--border-soft)] space-y-1.5">
                {agent.evidence.map((item, i) => (
                  <li
                    key={i}
                    className="text-xs leading-relaxed text-[var(--text-secondary)] pl-3 border-l-2 border-[var(--border-soft)]"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </div>
      </div>

      {/* Subtle technical footer */}
      {report.processing_ms !== null && (
        <p className="text-center text-xs text-[var(--text-muted)]">
          Investigation completed in {report.processing_ms}ms · Powered by{" "}
          {providerLabel(report.provider_used)}
        </p>
      )}
    </div>
  );
}
