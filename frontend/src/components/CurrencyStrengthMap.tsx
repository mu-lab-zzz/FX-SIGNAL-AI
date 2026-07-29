import React, { useEffect, useState } from "react";
import type { CurrencyStrength, CurrencyStrengthMap as CurrencyStrengthMapType } from "../types";
import { api } from "../utils/api";
import { starsToDisplay } from "../utils/format";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const TREND_ICON: Record<string, string> = {
  rising: "↑",
  falling: "↓",
  stable: "→",
};

const TREND_COLOR: Record<string, string> = {
  rising: "#22c55e",
  falling: "#ef4444",
  stable: "#9ca3af",
};

const scoreColor = (score: number): string => {
  if (score >= 30) return "#22c55e";
  if (score >= -10) return "#eab308";
  return "#ef4444";
};

export const CurrencyStrengthMapComponent: React.FC = () => {
  const [data, setData] = useState<CurrencyStrengthMapType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCurrencyStrength()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: "#9ca3af", padding: 20 }}>通貨強弱計算中...</div>;
  if (!data) return null;

  const chartData = [...data.strengths].sort((a, b) => b.score - a.score);

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 700, color: "#f3f4f6", marginBottom: 16 }}>
        通貨強弱マップ
      </div>

      {/* Bar chart */}
      <div style={{ height: 200, marginBottom: 20 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical">
            <XAxis
              type="number"
              domain={[-80, 80]}
              tick={{ fill: "#6b7280", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="currency"
              tick={{ fill: "#d1d5db", fontSize: 12, fontWeight: 700 }}
              tickLine={false}
              axisLine={false}
              width={36}
            />
            <Tooltip
              contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
              formatter={(v: number) => [`${v.toFixed(1)}`, "スコア"]}
            />
            <Bar dataKey="score" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={index} fill={scoreColor(entry.score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend table */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {data.strengths.map((ccy) => (
          <div
            key={ccy.currency}
            style={{
              display: "flex",
              alignItems: "center",
              background: "#1f2937",
              borderRadius: 8,
              padding: "8px 12px",
              gap: 10,
            }}
          >
            <div
              style={{
                width: 44,
                fontWeight: 900,
                fontSize: 14,
                color: scoreColor(ccy.score),
              }}
            >
              {ccy.currency}
            </div>
            <div style={{ flex: 1, fontSize: 13, color: "#eab308" }}>
              {starsToDisplay(ccy.stars)}
            </div>
            <div style={{ fontSize: 12, color: TREND_COLOR[ccy.trend] }}>
              {TREND_ICON[ccy.trend]}
            </div>
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: scoreColor(ccy.score),
                minWidth: 50,
                textAlign: "right",
              }}
            >
              {ccy.score.toFixed(1)}
            </div>
          </div>
        ))}
      </div>

      <div style={{ fontSize: 11, color: "#4b5563", marginTop: 12, textAlign: "right" }}>
        更新: {new Date(data.generated_at).toLocaleString("ja-JP")}
      </div>
    </div>
  );
};
