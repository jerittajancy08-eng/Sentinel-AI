"use client";

import type { AgentId, AgentResult, AgentStatus } from "@/lib/types";
import { AGENT_IDS, AGENT_LABELS } from "@/lib/types";

interface AgentNetworkDiagramProps {
  statuses: Record<AgentId, AgentStatus>;
  results: Partial<Record<AgentId, AgentResult>>;
  judgeStatus: AgentStatus;
  verdictReady: boolean;
}

const NODE_X: Record<AgentId, number> = {
  content_agent: 110,
  pattern_agent: 370,
  knowledge_agent: 630,
  identity_agent: 890,
};

const NODE_Y = 230;
const ORCH_X = 500;
const ORCH_Y = 60;
const JUDGE_X = 500;
const JUDGE_Y = 400;

function riskColor(score: number | undefined): string {
  if (score === undefined) return "var(--text-muted)";
  if (score >= 85) return "var(--risk-critical)";
  if (score >= 65) return "var(--risk-high)";
  if (score >= 40) return "var(--risk-medium)";
  if (score >= 20) return "var(--risk-low)";
  return "var(--risk-safe)";
}

function statusStroke(status: AgentStatus): string {
  switch (status) {
    case "running":
      return "var(--agent-cyan)";
    case "completed":
      return "var(--agent-cyan)";
    case "failed":
      return "var(--risk-critical)";
    default:
      return "var(--border)";
  }
}

export default function AgentNetworkDiagram({
  statuses,
  results,
  judgeStatus,
  verdictReady,
}: AgentNetworkDiagramProps) {
  return (
    <svg
      viewBox="0 0 1000 520"
      className="w-full h-auto"
      role="img"
      aria-label="Agent orchestration network diagram"
    >
      <defs>
        <marker
          id="arrow"
          markerWidth="8"
          markerHeight="8"
          refX="4"
          refY="4"
          orient="auto"
        >
          <path d="M0,0 L8,4 L0,8 Z" fill="var(--border)" />
        </marker>
      </defs>

      {/* Connections: Orchestrator -> Agents */}
      {AGENT_IDS.map((id) => {
        const active = statuses[id] === "running";
        return (
          <line
            key={`o-${id}`}
            x1={ORCH_X}
            y1={ORCH_Y + 34}
            x2={NODE_X[id]}
            y2={NODE_Y - 38}
            stroke={active ? "var(--agent-cyan)" : "var(--border)"}
            strokeWidth={active ? 2 : 1.5}
            strokeDasharray={active ? "6 6" : undefined}
            style={active ? { animation: "dash-flow 0.6s linear infinite" } : undefined}
          />
        );
      })}

      {/* Connections: Agents -> Judge */}
      {AGENT_IDS.map((id) => {
        const done = statuses[id] === "completed";
        return (
          <line
            key={`j-${id}`}
            x1={NODE_X[id]}
            y1={NODE_Y + 38}
            x2={JUDGE_X}
            y2={JUDGE_Y - 34}
            stroke={done ? "var(--agent-cyan)" : "var(--border)"}
            strokeWidth={done ? 2 : 1.5}
            strokeOpacity={done ? 0.7 : 0.5}
          />
        );
      })}

      {/* Connection: Judge -> Verdict */}
      <line
        x1={JUDGE_X}
        y1={JUDGE_Y + 34}
        x2={JUDGE_X}
        y2={JUDGE_Y + 80}
        stroke={verdictReady ? "var(--signal)" : "var(--border)"}
        strokeWidth={verdictReady ? 2 : 1.5}
        markerEnd="url(#arrow)"
      />

      {/* Orchestrator node */}
      <g>
        <rect
          x={ORCH_X - 90}
          y={ORCH_Y - 24}
          width={180}
          height={48}
          rx={10}
          fill="var(--surface)"
          stroke="var(--border)"
          strokeWidth={1.5}
        />
        <text
          x={ORCH_X}
          y={ORCH_Y - 1}
          textAnchor="middle"
          dominantBaseline="middle"
          className="font-display"
          fill="var(--text-primary)"
          fontSize="15"
          fontWeight={600}
        >
          Orchestrator
        </text>
        <text
          x={ORCH_X}
          y={ORCH_Y + 15}
          textAnchor="middle"
          dominantBaseline="middle"
          className="font-mono"
          fill="var(--text-muted)"
          fontSize="9"
          letterSpacing="0.05em"
        >
          SENDS TO ALL 4 AGENTS AT ONCE
        </text>
      </g>

      {/* Agent nodes */}
      {AGENT_IDS.map((id) => {
        const status = statuses[id];
        const result = results[id];
        const score = result?.risk_score;

        return (
          <g key={id}>
            <rect
              x={NODE_X[id] - 85}
              y={NODE_Y - 38}
              width={170}
              height={76}
              rx={12}
              fill="var(--surface)"
              stroke={statusStroke(status)}
              strokeWidth={status === "running" ? 2 : 1.5}
              style={
                status === "running"
                  ? { animation: "pulse-glow 1.4s ease-in-out infinite" }
                  : undefined
              }
            />
            <text
              x={NODE_X[id]}
              y={NODE_Y - 13}
              textAnchor="middle"
              dominantBaseline="middle"
              className="font-display"
              fill="var(--text-primary)"
              fontSize="14"
              fontWeight={600}
            >
              {AGENT_LABELS[id]}
            </text>

            {/* Status indicator */}
            {status === "pending" && (
              <text
                x={NODE_X[id]}
                y={NODE_Y + 12}
                textAnchor="middle"
                dominantBaseline="middle"
                className="font-mono"
                fill="var(--text-muted)"
                fontSize="10"
                letterSpacing="0.08em"
              >
                WAITING
              </text>
            )}
            {status === "running" && (
              <text
                x={NODE_X[id]}
                y={NODE_Y + 12}
                textAnchor="middle"
                dominantBaseline="middle"
                className="font-mono"
                fill="var(--agent-cyan)"
                fontSize="10"
                letterSpacing="0.08em"
                style={{ animation: "pulse-glow 1.4s ease-in-out infinite" }}
              >
                Checking…
              </text>
            )}
            {status === "completed" && score !== undefined && (
              <>
                <circle
                  cx={NODE_X[id] - 50}
                  cy={NODE_Y + 14}
                  r={5}
                  fill={riskColor(score)}
                />
                <text
                  x={NODE_X[id] - 38}
                  y={NODE_Y + 14}
                  dominantBaseline="middle"
                  className="font-display"
                  fill="var(--text-secondary)"
                  fontSize="10"
                >
                  Score
                </text>
                <text
                  x={NODE_X[id] + 35}
                  y={NODE_Y + 15}
                  textAnchor="end"
                  dominantBaseline="middle"
                  className="font-mono"
                  fill={riskColor(score)}
                  fontSize="15"
                  fontWeight={700}
                >
                  {score}
                </text>
              </>
            )}
            {status === "failed" && (
              <text
                x={NODE_X[id]}
                y={NODE_Y + 12}
                textAnchor="middle"
                dominantBaseline="middle"
                className="font-mono"
                fill="var(--risk-critical)"
                fontSize="10"
                letterSpacing="0.08em"
              >
                ERROR
              </text>
            )}
          </g>
        );
      })}

      {/* Judge node */}
      <g>
        <rect
          x={JUDGE_X - 100}
          y={JUDGE_Y - 34}
          width={200}
          height={68}
          rx={12}
          fill="var(--surface)"
          stroke={statusStroke(judgeStatus)}
          strokeWidth={judgeStatus === "running" ? 2 : 1.5}
          style={
            judgeStatus === "running"
              ? { animation: "pulse-glow 1.4s ease-in-out infinite" }
              : undefined
          }
        />
        <text
          x={JUDGE_X}
          y={JUDGE_Y - 9}
          textAnchor="middle"
          dominantBaseline="middle"
          className="font-display"
          fill="var(--text-primary)"
          fontSize="16"
          fontWeight={700}
        >
          Judge Agent
        </text>
        <text
          x={JUDGE_X}
          y={JUDGE_Y + 12}
          textAnchor="middle"
          dominantBaseline="middle"
          className="font-display"
          fill={judgeStatus === "running" ? "var(--agent-cyan)" : "var(--text-muted)"}
          fontSize="11"
          style={
            judgeStatus === "running"
              ? { animation: "pulse-glow 1.4s ease-in-out infinite" }
              : undefined
          }
        >
          {judgeStatus === "running"
            ? "Reviewing all 4 results…"
            : judgeStatus === "completed"
            ? "Decision made"
            : "Waiting for results"}
        </text>
      </g>

      {/* Verdict output marker */}
      <g>
        <circle
          cx={JUDGE_X}
          cy={JUDGE_Y + 86}
          r={6}
          fill={verdictReady ? "var(--signal)" : "var(--border)"}
        />
        <text
          x={JUDGE_X + 16}
          y={JUDGE_Y + 86}
          dominantBaseline="middle"
          className="font-display"
          fill={verdictReady ? "var(--signal)" : "var(--text-muted)"}
          fontSize="12"
        >
          {verdictReady ? "Report ready below ↓" : "Report will appear below"}
        </text>
      </g>
    </svg>
  );
}
