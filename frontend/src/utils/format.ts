import type { SignalDirection, SignalStrength } from "../types";

export function strengthColor(strength: SignalStrength): string {
  switch (strength) {
    case "STRONG": return "#22c55e";
    case "WATCH":  return "#eab308";
    default:       return "#6b7280";
  }
}

export function directionLabel(direction: SignalDirection): string {
  switch (direction) {
    case "BUY":  return "買い";
    case "SELL": return "売り";
    default:     return "中立";
  }
}

export function directionColor(direction: SignalDirection): string {
  switch (direction) {
    case "BUY":  return "#3b82f6";
    case "SELL": return "#ef4444";
    default:     return "#6b7280";
  }
}

export function starsToDisplay(stars: number): string {
  return "★".repeat(stars) + "☆".repeat(Math.max(0, 5 - stars));
}

export function formatPrice(price: number, pair: string): string {
  const decimals = pair.includes("JPY") ? 3 : 5;
  return price.toFixed(decimals);
}

export function formatScore(score: number): string {
  return score.toFixed(1);
}

export function scoreEmoji(score: number): string {
  if (score >= 80) return "🟢";
  if (score >= 65) return "🟡";
  return "⚪";
}

export function changeColor(change: number): string {
  return change >= 0 ? "#22c55e" : "#ef4444";
}
