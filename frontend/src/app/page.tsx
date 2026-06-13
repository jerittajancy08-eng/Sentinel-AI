"use client";

import { useRef, useState } from "react";
import AgentNetworkDiagram from "@/components/AgentNetworkDiagram";
import VerdictReport from "@/components/VerdictReport";
import { streamInvestigation } from "@/lib/api";
import {
  AGENT_DESCRIPTIONS,
  AGENT_IDS,
  AGENT_LABELS,
  type AgentId,
  type AgentResult,
  type AgentStatus,
  type InvestigationReport,
} from "@/lib/types";

const SAMPLES: { label: string; text: string }[] = [
  {
    label: "Lottery / KYC Phishing",
    text:
      "URGENT: Your SBI account will be suspended. Verify your KYC immediately at bit.ly/sbi-verify or face legal action. Congratulations! You may also be eligible for a ₹50,000 reward — claim now before it expires.",
  },
  {
    label: "Fake Job Offer",
    text:
      "Hiring now! Work from home, earn ₹1500 per day. Part-time data entry job, no experience needed. Pay a small ₹499 registration fee to receive your starter kit. Contact our HR team on WhatsApp to begin.",
  },
  {
    label: "Legitimate Message",
    text:
      "Hi team, just a reminder that the quarterly review meeting has been moved to Thursday at 2pm in Conference Room B. Please bring your updated project status reports.",
  },
];

const initialStatuses = (): Record<AgentId, AgentStatus> => ({
  content_agent: "pending",
  pattern_agent: "pending",
  knowledge_agent: "pending",
  identity_agent: "pending",
});

export default function Home() {
  const [text, setText] = useState("");
  const [phase, setPhase] = useState<"idle" | "investigating" | "complete" | "error">("idle");
  const [statuses, setStatuses] = useState<Record<AgentId, AgentStatus>>(initialStatuses());
  const [results, setResults] = useState<Partial<Record<AgentId, AgentResult>>>({});
  const [judgeStatus, setJudgeStatus] = useState<AgentStatus>("pending");
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const resultsRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function runInvestigation() {
    if (!text.trim() || phase === "investigating") return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setPhase("investigating");
    setStatuses({
      content_agent: "running",
      pattern_agent: "running",
      knowledge_agent: "running",
      identity_agent: "running",
    });
    setResults({});
    setJudgeStatus("pending");
    setReport(null);
    setErrorMsg(null);

    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);

    try {
      await streamInvestigation(
        text,
        (event) => {
          if (event.event === "agent_completed" && event.agent && event.result) {
            setStatuses((prev) => ({ ...prev, [event.agent as AgentId]: "completed" }));
            setResults((prev) => ({ ...prev, [event.agent as AgentId]: event.result }));
          } else if (event.event === "agent_failed" && event.agent) {
            setStatuses((prev) => ({ ...prev, [event.agent as AgentId]: "failed" }));
          } else if (event.event === "judge_started") {
            setJudgeStatus("running");
          } else if (event.event === "investigation_complete" && event.report) {
            setJudgeStatus("completed");
            setReport(event.report);
            setPhase("complete");
          }
        },
        controller.signal
      );
    } catch (err) {
      if (controller.signal.aborted) return;
      setErrorMsg(
        err instanceof Error
          ? `${err.message} — is the Sentinel AI backend running on port 8000?`
          : "Investigation failed."
      );
      setPhase("error");
    }
  }

  return (
    <main className="min-h-screen bg-[var(--bg)]">
      {/* ───────────── Hero ───────────── */}
      <section className="scan-grid border-b border-[var(--border-soft)]">
        <div className="max-w-6xl mx-auto px-6 pt-20 pb-16 md:pt-28 md:pb-24">
          <div className="flex items-center gap-2 mb-6">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: "var(--signal)" }}
            />
            <span className="font-mono text-xs tracking-[0.2em] text-[var(--text-secondary)]">
              MICROSOFT AGENTS LEAGUE · REASONING AGENTS TRACK
            </span>
          </div>

          <h1 className="font-display text-4xl sm:text-5xl md:text-6xl font-bold leading-[1.05] tracking-tight text-[var(--text-primary)] max-w-3xl text-balance">
            Four agents investigate.
            <br />
            <span style={{ color: "var(--signal)" }}>One judge decides.</span>
          </h1>

          <p className="mt-6 text-base md:text-lg text-[var(--text-secondary)] max-w-2xl leading-relaxed">
            Sentinel AI is a multi-agent scam investigation network built on Microsoft
            Foundry. Paste any suspicious email, SMS, or offer — independent
            specialist agents analyze it in parallel, and a Judge Agent
            reasons over their findings to deliver a grounded, explainable
            verdict.
          </p>

          <div className="mt-12">
            <AgentNetworkDiagram
              statuses={statuses}
              results={results}
              judgeStatus={judgeStatus}
              verdictReady={phase === "complete"}
            />
          </div>
        </div>
      </section>

      {/* ───────────── Investigation input ───────────── */}
      <section className="max-w-6xl mx-auto px-6 py-14 md:py-20">
        <div className="grid lg:grid-cols-[1.3fr_1fr] gap-10">
          <div>
            <h2 className="font-display text-2xl md:text-3xl font-bold text-[var(--text-primary)] mb-2">
              Start an investigation
            </h2>
            <p className="text-[var(--text-secondary)] text-sm mb-6">
              Paste a suspicious email, SMS, WhatsApp message, or offer below.
            </p>

            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste suspicious message text here…"
              rows={7}
              className="w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-4 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] font-mono leading-relaxed resize-none focus:border-[var(--agent-cyan)]"
            />

            <div className="mt-4 flex items-center gap-3 flex-wrap">
              <button
                onClick={runInvestigation}
                disabled={!text.trim() || phase === "investigating"}
                className="font-display font-semibold text-sm px-6 py-3 rounded-[var(--radius-md)] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                style={{
                  backgroundColor: "var(--signal)",
                  color: "#1A1306",
                }}
              >
                {phase === "investigating" ? "Investigating…" : "Run Investigation"}
              </button>

              {phase === "investigating" && (
                <span
                  className="font-mono text-xs text-[var(--agent-cyan)]"
                  style={{ animation: "pulse-glow 1.4s ease-in-out infinite" }}
                >
                  4 agents working in parallel…
                </span>
              )}
            </div>

            {errorMsg && (
              <p className="mt-4 text-sm text-[var(--risk-critical)] font-mono">
                {errorMsg}
              </p>
            )}
          </div>

          {/* Sample messages + agent roster */}
          <div className="space-y-6">
            <div>
              <h3 className="font-display text-sm font-semibold tracking-wide text-[var(--text-primary)] mb-3">
                TRY A SAMPLE
              </h3>
              <div className="flex flex-col gap-2">
                {SAMPLES.map((sample) => (
                  <button
                    key={sample.label}
                    onClick={() => setText(sample.text)}
                    className="text-left rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text-secondary)] hover:border-[var(--agent-cyan)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-display text-sm font-semibold tracking-wide text-[var(--text-primary)] mb-3">
                THE AGENT ROSTER
              </h3>
              <div className="flex flex-col gap-2">
                {AGENT_IDS.map((id) => (
                  <div
                    key={id}
                    className="rounded-[var(--radius-md)] border border-[var(--border-soft)] bg-[var(--bg-elevated)] px-4 py-3"
                  >
                    <p className="font-display text-sm font-semibold text-[var(--text-primary)]">
                      {AGENT_LABELS[id]}
                    </p>
                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                      {AGENT_DESCRIPTIONS[id]}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ───────────── Results ───────────── */}
      {(phase === "complete" || phase === "investigating") && (
        <section
          ref={resultsRef}
          className="max-w-6xl mx-auto px-6 py-14 md:py-20 border-t border-[var(--border-soft)]"
        >
          <h2 className="font-display text-2xl md:text-3xl font-bold text-[var(--text-primary)] mb-8">
            Scam Risk Report
          </h2>

          {report ? (
            <VerdictReport report={report} />
          ) : (
            <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
              <p
                className="font-mono text-sm text-[var(--agent-cyan)]"
                style={{ animation: "pulse-glow 1.4s ease-in-out infinite" }}
              >
                Agents are analyzing the message — results will appear as
                each agent completes…
              </p>
            </div>
          )}
        </section>
      )}

      {/* ───────────── Footer ───────────── */}
      <footer className="border-t border-[var(--border-soft)]">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="font-mono text-xs text-[var(--text-muted)]">
            SENTINEL AI · Multi-Agent Scam Investigation Network
          </p>
          <p className="font-mono text-xs text-[var(--text-muted)]">
            Built on Microsoft Foundry · Reasoning Agents Track
          </p>
        </div>
      </footer>
    </main>
  );
}
