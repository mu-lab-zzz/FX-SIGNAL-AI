import React, { useEffect, useState } from "react";
import type { RankingResponse } from "../types";
import { api } from "../utils/api";
import { PairRankCard } from "../components/PairRankCard";
import { SignalDetail } from "../components/SignalDetail";
import { CurrencyStrengthMapComponent } from "../components/CurrencyStrengthMap";
import { NewsPanel } from "../components/NewsPanel";
import { BacktestPanel } from "../components/BacktestPanel";

type Tab = "signal" | "backtest";

const NAV_TABS: { key: Tab; label: string }[] = [
  { key: "signal", label: "シグナル詳細" },
  { key: "backtest", label: "バックテスト" },
];

export const Dashboard: React.FC = () => {
  const [ranking, setRanking] = useState<RankingResponse | null>(null);
  const [selectedPair, setSelectedPair] = useState<string>("USD/JPY");
  const [activeTab, setActiveTab] = useState<Tab>("signal");
  const [rankLoading, setRankLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const loadRanking = () => {
    setRankLoading(true);
    api.getRanking()
      .then((r) => {
        setRanking(r);
        setLastUpdated(new Date());
      })
      .finally(() => setRankLoading(false));
  };

  useEffect(() => {
    loadRanking();
    const interval = setInterval(loadRanking, 5 * 60 * 1000); // refresh every 5min
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#111827",
        color: "#f3f4f6",
        fontFamily: "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
      }}
    >
      {/* Top header */}
      <div
        style={{
          background: "#0f172a",
          borderBottom: "1px solid #1f2937",
          padding: "0 20px",
          height: 56,
          display: "flex",
          alignItems: "center",
          gap: 12,
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ fontSize: 20, fontWeight: 900, letterSpacing: -0.5 }}>
          📡 FX Signal AI
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: 11, color: "#4b5563" }}>
          更新: {lastUpdated.toLocaleTimeString("ja-JP")}
        </div>
        <button
          onClick={loadRanking}
          style={{
            background: "#1d4ed8",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            padding: "6px 14px",
            fontSize: 12,
            cursor: "pointer",
          }}
        >
          更新
        </button>
      </div>

      {/* Main layout */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "300px 1fr 280px",
          height: "calc(100vh - 56px)",
          overflow: "hidden",
        }}
      >
        {/* Left: Ranking */}
        <div
          style={{
            borderRight: "1px solid #1f2937",
            overflowY: "auto",
            padding: 16,
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 700, color: "#9ca3af", marginBottom: 12 }}>
            ペアランキング {rankLoading ? "⟳" : ""}
          </div>
          {ranking?.rankings.map((r) => (
            <div key={r.pair} style={{ marginBottom: 8 }}>
              <PairRankCard
                ranking={r}
                isSelected={selectedPair === r.pair}
                onClick={() => {
                  setSelectedPair(r.pair);
                  setActiveTab("signal");
                }}
              />
            </div>
          ))}
          {!ranking && !rankLoading && (
            <div style={{ color: "#4b5563", fontSize: 13 }}>データなし</div>
          )}
        </div>

        {/* Center: Detail panel */}
        <div
          style={{
            overflowY: "auto",
            padding: 20,
          }}
        >
          {/* Tab nav */}
          <div style={{ display: "flex", gap: 4, marginBottom: 20 }}>
            {NAV_TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                style={{
                  background: activeTab === t.key ? "#1d4ed8" : "#1f2937",
                  color: activeTab === t.key ? "#fff" : "#9ca3af",
                  border: "none",
                  borderRadius: 8,
                  padding: "7px 16px",
                  fontSize: 13,
                  cursor: "pointer",
                  fontWeight: activeTab === t.key ? 700 : 400,
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {activeTab === "signal" && <SignalDetail pair={selectedPair} />}
          {activeTab === "backtest" && <BacktestPanel pair={selectedPair} />}
        </div>

        {/* Right: Sidebar */}
        <div
          style={{
            borderLeft: "1px solid #1f2937",
            overflowY: "auto",
            padding: 16,
          }}
        >
          <div style={{ marginBottom: 28 }}>
            <CurrencyStrengthMapComponent />
          </div>
          <NewsPanel />
        </div>
      </div>
    </div>
  );
};
