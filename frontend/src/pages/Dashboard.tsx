import React, { useCallback, useEffect, useRef, useState } from "react";
import type { RankingResponse, PairRanking } from "../types";
import { api } from "../utils/api";
import { PairRankCard } from "../components/PairRankCard";
import { SignalDetail } from "../components/SignalDetail";
import { CurrencyStrengthMapComponent } from "../components/CurrencyStrengthMap";
import { NewsPanel } from "../components/NewsPanel";
import { BacktestPanel } from "../components/BacktestPanel";
import { AuthModal } from "../components/AuthModal";
import { AlertBanner } from "../components/AlertBanner";
import { useWebSocket, WsTick, WsAlert } from "../hooks/useWebSocket";
import { useAuth } from "../hooks/useAuth";
import { useNotifications } from "../hooks/useNotifications";
import { scoreEmoji, strengthColor } from "../utils/format";

type Tab = "signal" | "backtest";
type SideTab = "strength" | "news";

const NAV_TABS: { key: Tab; label: string }[] = [
  { key: "signal",   label: "シグナル詳細" },
  { key: "backtest", label: "バックテスト"  },
];

const SIDE_TABS: { key: SideTab; label: string }[] = [
  { key: "strength", label: "通貨強弱" },
  { key: "news",     label: "ニュース"  },
];

// ── Responsive breakpoint ─────────────────────────────────────────────────────
function useIsMobile() {
  const [mobile, setMobile] = useState(window.innerWidth < 768);
  useEffect(() => {
    const h = () => setMobile(window.innerWidth < 768);
    window.addEventListener("resize", h);
    return () => window.removeEventListener("resize", h);
  }, []);
  return mobile;
}

export const Dashboard: React.FC = () => {
  const isMobile = useIsMobile();
  const { user, loading: authLoading, logout } = useAuth();
  const { permission, requestPermission, notify } = useNotifications();

  const [ranking, setRanking]           = useState<RankingResponse | null>(null);
  const [liveTicks, setLiveTicks]       = useState<Record<string, WsTick>>({});
  const [selectedPair, setSelectedPair] = useState("USD/JPY");
  const [activeTab, setActiveTab]       = useState<Tab>("signal");
  const [activeSideTab, setActiveSideTab] = useState<SideTab>("strength");
  const [rankLoading, setRankLoading]   = useState(true);
  const [lastUpdated, setLastUpdated]   = useState(new Date());
  const [showAuth, setShowAuth]         = useState(false);
  const [latestAlert, setLatestAlert]   = useState<WsAlert | null>(null);
  const [mobilePanel, setMobilePanel]   = useState<"list" | "detail" | "side">("list");

  // ── WebSocket ─────────────────────────────────────────────────────────────
  const handleTicks = useCallback((ticks: WsTick[]) => {
    setLiveTicks((prev) => {
      const next = { ...prev };
      for (const t of ticks) next[t.pair] = t;
      return next;
    });
    setLastUpdated(new Date());
  }, []);

  const handleAlert = useCallback((alert: WsAlert) => {
    setLatestAlert(alert);
    notify(`📡 ${alert.pair} シグナル`, alert.message);
  }, [notify]);

  const { connected } = useWebSocket(handleTicks, handleAlert);

  // ── Ranking (initial + polling fallback) ─────────────────────────────────
  const loadRanking = useCallback(() => {
    setRankLoading(true);
    api.getRanking()
      .then((r) => { setRanking(r); setLastUpdated(new Date()); })
      .finally(() => setRankLoading(false));
  }, []);

  useEffect(() => {
    loadRanking();
    const interval = setInterval(loadRanking, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadRanking]);

  // Merge WS live ticks into ranking for real-time price + score
  const mergedRankings: PairRanking[] = (ranking?.rankings ?? []).map((r) => {
    const tick = liveTicks[r.pair];
    if (!tick) return r;
    return {
      ...r,
      score:      tick.score,
      direction:  tick.direction as any,
      strength:   tick.strength as any,
      change_24h: tick.change_pct,
    };
  });

  // ── Styles ────────────────────────────────────────────────────────────────
  const tabBtn = (active: boolean): React.CSSProperties => ({
    background: active ? "#1d4ed8" : "#1f2937",
    color:      active ? "#fff"    : "#9ca3af",
    border: "none",
    borderRadius: 8,
    padding: "7px 14px",
    fontSize: 13,
    cursor: "pointer",
    fontWeight: active ? 700 : 400,
  });

  const column: React.CSSProperties = {
    overflowY: "auto",
    padding: 16,
  };

  // ── Mobile bottom nav ─────────────────────────────────────────────────────
  const MobileNav = () => (
    <div style={{
      position: "fixed", bottom: 0, left: 0, right: 0,
      background: "#0f172a",
      borderTop: "1px solid #1f2937",
      display: "flex",
      zIndex: 100,
    }}>
      {(["list","detail","side"] as const).map((panel) => {
        const labels: Record<string, string> = { list: "📋 ランク", detail: "📊 詳細", side: "🗺 分析" };
        const active = mobilePanel === panel;
        return (
          <button
            key={panel}
            onClick={() => setMobilePanel(panel)}
            style={{
              flex: 1,
              padding: "12px 0",
              background: active ? "#1d4ed8" : "transparent",
              border: "none",
              color: active ? "#fff" : "#6b7280",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            {labels[panel]}
          </button>
        );
      })}
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "#111827", color: "#f3f4f6",
      fontFamily: "'Segoe UI','Helvetica Neue',Arial,sans-serif" }}>

      {/* Alert banner */}
      <AlertBanner alert={latestAlert} />

      {/* Auth modal */}
      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

      {/* Header */}
      <div style={{
        background: "#0f172a",
        borderBottom: "1px solid #1f2937",
        padding: "0 16px",
        height: 56,
        display: "flex",
        alignItems: "center",
        gap: 10,
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ fontSize: 18, fontWeight: 900 }}>📡 FX Signal AI</div>

        {/* WS indicator */}
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          background: connected ? "#22c55e" : "#ef4444",
        }} title={connected ? "ライブ接続中" : "接続中..."} />

        <div style={{ flex: 1 }} />

        {/* Notification bell */}
        <button
          onClick={requestPermission}
          title={permission === "granted" ? "通知ON" : "通知を許可する"}
          style={{
            background: "none", border: "none",
            color: permission === "granted" ? "#22c55e" : "#6b7280",
            fontSize: 18, cursor: "pointer",
          }}
        >
          🔔
        </button>

        {/* Updated time */}
        {!isMobile && (
          <div style={{ fontSize: 11, color: "#4b5563" }}>
            {lastUpdated.toLocaleTimeString("ja-JP")}
          </div>
        )}

        {/* Auth */}
        {authLoading ? null : user ? (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ fontSize: 12, color: "#9ca3af" }}>{user.display_name || user.email}</div>
            <button onClick={logout}
              style={{ background: "#374151", border: "none", borderRadius: 6,
                color: "#d1d5db", padding: "4px 10px", fontSize: 12, cursor: "pointer" }}>
              ログアウト
            </button>
          </div>
        ) : (
          <button onClick={() => setShowAuth(true)}
            style={{ background: "#1d4ed8", color: "#fff", border: "none",
              borderRadius: 6, padding: "6px 14px", fontSize: 12, cursor: "pointer" }}>
            ログイン
          </button>
        )}
      </div>

      {/* ── Desktop layout ── */}
      {!isMobile ? (
        <div style={{
          display: "grid",
          gridTemplateColumns: "280px 1fr 264px",
          height: "calc(100vh - 56px)",
          overflow: "hidden",
        }}>
          {/* Left: Ranking */}
          <div style={{ ...column, borderRight: "1px solid #1f2937" }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#6b7280",
              letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>
              ペアランキング {rankLoading && "⟳"}
            </div>
            {mergedRankings.map((r) => (
              <div key={r.pair} style={{ marginBottom: 8 }}>
                <PairRankCard
                  ranking={r}
                  isSelected={selectedPair === r.pair}
                  onClick={() => { setSelectedPair(r.pair); setActiveTab("signal"); }}
                />
              </div>
            ))}
          </div>

          {/* Center */}
          <div style={{ ...column }}>
            <div style={{ display: "flex", gap: 4, marginBottom: 20 }}>
              {NAV_TABS.map((t) => (
                <button key={t.key} onClick={() => setActiveTab(t.key)} style={tabBtn(activeTab === t.key)}>
                  {t.label}
                </button>
              ))}
            </div>
            {activeTab === "signal"   && <SignalDetail pair={selectedPair} />}
            {activeTab === "backtest" && <BacktestPanel pair={selectedPair} />}
          </div>

          {/* Right sidebar */}
          <div style={{ ...column, borderLeft: "1px solid #1f2937" }}>
            <div style={{ display: "flex", gap: 4, marginBottom: 16 }}>
              {SIDE_TABS.map((t) => (
                <button key={t.key} onClick={() => setActiveSideTab(t.key)} style={tabBtn(activeSideTab === t.key)}>
                  {t.label}
                </button>
              ))}
            </div>
            {activeSideTab === "strength" && <CurrencyStrengthMapComponent />}
            {activeSideTab === "news"     && <NewsPanel />}
          </div>
        </div>
      ) : (
        /* ── Mobile layout ── */
        <div style={{ height: "calc(100vh - 56px - 50px)", overflowY: "auto", padding: 12 }}>
          {mobilePanel === "list" && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#6b7280",
                textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>
                ペアランキング {rankLoading && "⟳"}
              </div>
              {mergedRankings.map((r) => (
                <div key={r.pair} style={{ marginBottom: 8 }}>
                  <PairRankCard
                    ranking={r}
                    isSelected={selectedPair === r.pair}
                    onClick={() => { setSelectedPair(r.pair); setMobilePanel("detail"); }}
                  />
                </div>
              ))}
            </div>
          )}
          {mobilePanel === "detail" && (
            <div>
              <div style={{ display: "flex", gap: 4, marginBottom: 16 }}>
                {NAV_TABS.map((t) => (
                  <button key={t.key} onClick={() => setActiveTab(t.key)} style={tabBtn(activeTab === t.key)}>
                    {t.label}
                  </button>
                ))}
              </div>
              {activeTab === "signal"   && <SignalDetail pair={selectedPair} />}
              {activeTab === "backtest" && <BacktestPanel pair={selectedPair} />}
            </div>
          )}
          {mobilePanel === "side" && (
            <div>
              <div style={{ display: "flex", gap: 4, marginBottom: 16 }}>
                {SIDE_TABS.map((t) => (
                  <button key={t.key} onClick={() => setActiveSideTab(t.key)} style={tabBtn(activeSideTab === t.key)}>
                    {t.label}
                  </button>
                ))}
              </div>
              {activeSideTab === "strength" && <CurrencyStrengthMapComponent />}
              {activeSideTab === "news"     && <NewsPanel />}
            </div>
          )}
          <MobileNav />
        </div>
      )}
    </div>
  );
};
