import React from "react";
import type { PairRanking } from "../types";
import {
  strengthColor,
  directionLabel,
  directionColor,
  scoreEmoji,
  changeColor,
} from "../utils/format";

interface Props {
  ranking: PairRanking;
  onClick: () => void;
  isSelected: boolean;
}

const RANK_BADGE: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

export const PairRankCard: React.FC<Props> = ({ ranking, onClick, isSelected }) => {
  const { rank, pair, score, direction, strength, change_24h } = ranking;
  const badge = RANK_BADGE[rank] || `#${rank}`;
  const borderColor = isSelected ? "#3b82f6" : "transparent";

  return (
    <div
      onClick={onClick}
      style={{
        background: "#1f2937",
        borderRadius: 12,
        padding: "14px 16px",
        cursor: "pointer",
        border: `2px solid ${borderColor}`,
        transition: "border-color 0.2s, transform 0.15s",
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      {/* Rank */}
      <div style={{ fontSize: 22, minWidth: 36, textAlign: "center" }}>{badge}</div>

      {/* Pair + change */}
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 700, fontSize: 15, color: "#f3f4f6" }}>{pair}</div>
        <div style={{ fontSize: 12, color: changeColor(change_24h) }}>
          {change_24h >= 0 ? "+" : ""}{change_24h.toFixed(3)}%
        </div>
      </div>

      {/* Score */}
      <div style={{ textAlign: "right" }}>
        <div style={{ fontSize: 22, fontWeight: 800, color: strengthColor(strength) }}>
          {scoreEmoji(score)} {Math.round(score)}
        </div>
        <div
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: directionColor(direction),
            background: `${directionColor(direction)}22`,
            borderRadius: 6,
            padding: "2px 6px",
            marginTop: 2,
          }}
        >
          {directionLabel(direction)}
        </div>
      </div>
    </div>
  );
};
