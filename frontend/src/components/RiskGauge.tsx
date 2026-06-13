"use client";

interface RiskGaugeProps {
  score: number;
  riskLevel: string;
}

function riskColor(score: number): string {
  if (score >= 85) return "var(--risk-critical)";
  if (score >= 65) return "var(--risk-high)";
  if (score >= 40) return "var(--risk-medium)";
  if (score >= 20) return "var(--risk-low)";
  return "var(--risk-safe)";
}

export default function RiskGauge({ score, riskLevel }: RiskGaugeProps) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference * (1 - clamped / 100);
  const color = riskColor(clamped);

  return (
    <div className="relative w-44 h-44 shrink-0">
      <svg viewBox="0 0 160 160" className="w-full h-full -rotate-90">
        <circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth="10"
        />
        <circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-4xl font-bold" style={{ color }}>
          {clamped}
        </span>
        <span className="font-mono text-xs tracking-widest text-[var(--text-muted)] mt-1">
          / 100
        </span>
        <span
          className="font-display text-xs font-semibold tracking-wide mt-2 px-2 py-0.5 rounded-full"
          style={{ color, backgroundColor: `${color}1A` }}
        >
          {riskLevel}
        </span>
      </div>
    </div>
  );
}
