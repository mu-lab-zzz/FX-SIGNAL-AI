import React, { useEffect, useState } from "react";
import type { BacktestResult } from "../types";
import { api } from "../utils/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface Props {
  pair: string;
}

const MetricCard: React.FC<{ label: string; value: string; highlight?: boolean }> = ({
  label,
  value,
  highlight,
}) => (
  <div
    style={{
      background: "#1f2937",
      borderRadius: 8,
      padding: "10px 14px",
      textAlign: "center",
    }}
  >
    <div style={{ fontSize: 20, fontWeight: 800, color: highlight ? "#22c55e" : "#f3f4f6" }}>
      {value}
    </div>
    <div style={{ fontSize: 11, color: "#6b7280" }}>{label}</div>
  </div>
);

export const BacktestPanel: React.FC<Props> = ({ pair }) => {
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [years, setYears] = useState(5);

  const run = () => {
    setLoading(true);
    api.getBacktest(pair, years)
      .then(setResult)
      .finally(() => setLoading(false));
  };

  useEffect(() => { run(); }, [pair, years]);

  if (loading) return <div style={{ color: "#9ca3af", padding: 20 }}>バックテスト実行中 ({pair})...</div>;
  if (!result) return null;

  // Cumulative pips curve
  let cum = 0;
  const curveData = result.trades.map((t, i) => {
    cum += t.pips;
    return { i: i + 1, pips: parseFloat(cum.toFixed(1)) };
  });

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: "#f3f4f6" }}>
          バックテスト — {pair}
        </div>
        <select
          value={years}
          onChange={(e) => setYears(Number(e.target.value))}
          style={{
            background: "#374151",
            color: "#f3f4f6",
            border: "none",
            borderRadius: 6,
            padding: "4px 8px",
            fontSize: 12,
          }}
        >
          {[1, 3, 5, 7].map((y) => (
            <option key={y} value={y}>{y}年</option>
          ))}
        </select>
        <div style={{ fontSize: 11, color: "#6b7280" }}>
          {result.start_date.slice(0, 10)} ～ {result.end_date.slice(0, 10)}
        </div>
      </div>

      {/* Metrics grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginBottom: 20 }}>
        <MetricCard label="総トレード数" value={String(result.total_trades)} />
        <MetricCard label="勝率" value={`${result.win_rate.toFixed(1)}%`} highlight={result.win_rate >= 50} />
        <MetricCard label="PF" value={result.profit_factor === Infinity ? "∞" : result.profit_factor.toFixed(2)} highlight={result.profit_factor >= 1.5} />
        <MetricCard label="平均利益" value={`+${result.avg_profit_pips}pips`} />
        <MetricCard label="平均損失" value={`-${result.avg_loss_pips}pips`} />
        <MetricCard label="最大連敗" value={String(result.max_consecutive_losses)} />
        <MetricCard label="最大DD" value={`${result.max_drawdown_pct.toFixed(1)}%`} />
        <MetricCard label="シャープ比" value={result.sharpe_ratio.toFixed(3)} highlight={result.sharpe_ratio >= 0.5} />
        <MetricCard label="総リターン" value={`${result.total_return_pct.toFixed(2)}%`} highlight={result.total_return_pct > 0} />
      </div>

      {/* Equity curve */}
      {curveData.length > 1 && (
        <div>
          <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 8 }}>累積損益 (pips)</div>
          <div style={{ height: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={curveData}>
                <XAxis dataKey="i" tick={false} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fill: "#6b7280", fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                  formatter={(v: number) => [`${v}`, "累積pips"]}
                />
                <ReferenceLine y={0} stroke="#374151" strokeDasharray="4 4" />
                <Line
                  type="monotone"
                  dataKey="pips"
                  stroke={curveData[curveData.length - 1]?.pips >= 0 ? "#22c55e" : "#ef4444"}
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {result.total_trades === 0 && (
        <div style={{ color: "#6b7280", textAlign: "center", padding: 20 }}>
          この期間にシグナルが発生しませんでした
        </div>
      )}
    </div>
  );
};
