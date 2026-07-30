import React, { useState } from "react";
import { useAuth } from "../hooks/useAuth";

const ALL_PAIRS = [
  "USD/JPY", "EUR/USD", "GBP/USD",
  "AUD/JPY", "EUR/JPY", "NZD/JPY",
  "AUD/USD", "GBP/JPY", "USD/CHF",
];

export const SettingsPanel: React.FC = () => {
  const { user, updateAlerts } = useAuth();
  const [pairs, setPairs]       = useState<string[]>(user?.alert_pairs ?? []);
  const [minScore, setMinScore] = useState(user?.alert_min_score ?? 80);
  const [saving, setSaving]     = useState(false);
  const [saved, setSaved]       = useState(false);

  const togglePair = (pair: string) =>
    setPairs((prev) =>
      prev.includes(pair) ? prev.filter((p) => p !== pair) : [...prev, pair]
    );

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateAlerts(pairs, minScore);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  if (!user) return (
    <div style={{ color: "#6b7280", fontSize: 13, padding: 16 }}>
      ログインするとアラート設定を保存できます。
    </div>
  );

  return (
    <div style={{ color: "#f3f4f6" }}>
      <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 20 }}>
        アラート設定
      </div>

      {/* Min score slider */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between",
          fontSize: 13, marginBottom: 8 }}>
          <span style={{ color: "#d1d5db" }}>最低スコア閾値</span>
          <span style={{ fontWeight: 800, color: "#22c55e" }}>{minScore}点以上</span>
        </div>
        <input
          type="range" min={60} max={95} step={5}
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
          style={{ width: "100%", accentColor: "#1d4ed8" }}
        />
        <div style={{ display: "flex", justifyContent: "space-between",
          fontSize: 10, color: "#4b5563", marginTop: 2 }}>
          <span>60 (緩め)</span>
          <span>80 (推奨)</span>
          <span>95 (厳格)</span>
        </div>
      </div>

      {/* Pair checkboxes */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 13, color: "#d1d5db", marginBottom: 10 }}>
          通知するペア{" "}
          <span style={{ fontSize: 11, color: "#6b7280" }}>
            (未選択 = 全ペア)
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
          {ALL_PAIRS.map((pair) => {
            const checked = pairs.includes(pair);
            return (
              <label key={pair} style={{
                display: "flex", alignItems: "center", gap: 8,
                background: checked ? "#1e3a5f" : "#1f2937",
                border: `1px solid ${checked ? "#3b82f6" : "transparent"}`,
                borderRadius: 8, padding: "8px 10px", cursor: "pointer",
                fontSize: 13, color: checked ? "#93c5fd" : "#9ca3af",
              }}>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => togglePair(pair)}
                  style={{ accentColor: "#3b82f6" }}
                />
                {pair}
              </label>
            );
          })}
        </div>
      </div>

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={saving}
        style={{
          width: "100%", background: saved ? "#15803d" : "#1d4ed8",
          color: "#fff", border: "none", borderRadius: 8,
          padding: "11px 0", fontSize: 14, fontWeight: 700,
          cursor: saving ? "not-allowed" : "pointer",
          transition: "background 0.3s",
        }}
      >
        {saving ? "保存中..." : saved ? "✓ 保存しました" : "設定を保存"}
      </button>

      <div style={{ fontSize: 11, color: "#4b5563", marginTop: 10 }}>
        設定はWebSocket接続時に自動で適用されます。
      </div>
    </div>
  );
};
