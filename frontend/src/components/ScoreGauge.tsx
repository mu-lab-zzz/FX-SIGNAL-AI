import React from "react";

interface Props {
  score: number;
  label?: string;
  size?: number;
}

export const ScoreGauge: React.FC<Props> = ({ score, label, size = 120 }) => {
  const r = 45;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = Math.PI * r;  // half circle
  const dashOffset = circumference * (1 - score / 100);

  const color =
    score >= 80 ? "#22c55e" :
    score >= 65 ? "#eab308" :
    "#6b7280";

  return (
    <div style={{ textAlign: "center", display: "inline-block" }}>
      <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
        {/* Background arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#374151"
          strokeWidth="10"
          strokeLinecap="round"
        />
        {/* Foreground arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        {/* Score text */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          fontSize={size * 0.22}
          fontWeight="bold"
          fill={color}
        >
          {Math.round(score)}
        </text>
        <text
          x={cx}
          y={cy + 12}
          textAnchor="middle"
          fontSize={size * 0.11}
          fill="#9ca3af"
        >
          / 100
        </text>
      </svg>
      {label && (
        <div style={{ fontSize: 11, color: "#9ca3af", marginTop: -4 }}>{label}</div>
      )}
    </div>
  );
};
