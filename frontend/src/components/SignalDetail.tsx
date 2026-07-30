import React, { useEffect, useState } from "react";
import type { FXSignal } from "../types";
import { api } from "../utils/api";
import {
  directionLabel,
  directionColor,
  strengthColor,
  scoreEmoji,
  formatPrice,
} from "../utils/format";
import { ScoreGauge } from "./ScoreGauge";
import { PriceChart } from "./PriceChart";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface Props {
  pair: string;
}

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ marginBottom: 20 }}>
    <div
      style={{
        fontSize: 12,
        fontWeight: 700,
        color: "#6b7280",
        textTransform: "uppercase",
        letterSpacing: 1,
        marginBottom: 8,
        borderBottom: "1px solid #374151",
        paddingBottom: 4,
      }}
    >
      {title}
    </div>
    {children}
  </div>
);

const ScoreBar: React.FC<{ label: string; value: number; max: number; detail: string }> = ({
  label,
  value,
  max,
  detail,
}) => {
  const pct = (value / max) * 100;
  const color = pct >= 66 ? "#22c55e" : pct >= 33 ? "#eab308" : "#ef4444";
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
        <span style={{ fontSize: 12, color: "#d1d5db" }}>{label}</span>
        <span style={{ fontSize: 12, fontWeight: 700, color }}>
          {value.toFixed(1)} / {max}
        </span>
      </div>
      <div style={{ background: "#374151", borderRadius: 4, height: 6 }}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: 4,
            transition: "width 0.6s ease",
          }}
        />
      </div>
      <div style={{ fontSize: 10, color: "#6b7280", marginTop: 2 }}>{detail}</div>
    </div>
  );
};

export const SignalDetail: React.FC<Props> = ({ pair }) => {
  const [signal, setSignal] = useState<FXSignal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getSignal(pair)
      .then(setSignal)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [pair]);

  if (loading) return (
    <div style={{ color: "#9ca3af", padding: 40, textAlign: "center" }}>
      分析中... {pair}
    </div>
  );
  if (error) return (
    <div style={{ color: "#ef4444", padding: 20 }}>エラー: {error}</div>
  );
  if (!signal) return null;

  const radarData = [
    { subject: "トレンド", value: (signal.technical.trend_score / 20) * 100, fullMark: 100 },
    { subject: "MACD",    value: (signal.technical.macd_score / 15) * 100,   fullMark: 100 },
    { subject: "RSI",     value: (signal.technical.rsi_score / 10) * 100,    fullMark: 100 },
    { subject: "BB",      value: (signal.technical.bollinger_score / 10) * 100, fullMark: 100 },
    { subject: "金利差",  value: (signal.fundamental.interest_rate_score / 15) * 100, fullMark: 100 },
    { subject: "中銀",    value: (signal.fundamental.central_bank_score / 10) * 100,  fullMark: 100 },
    { subject: "経済",    value: (signal.fundamental.economic_score / 10) * 100,       fullMark: 100 },
  ];

  return (
    <div style={{ color: "#f3f4f6" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <div>
          <div style={{ fontSize: 28, fontWeight: 900 }}>{pair}</div>
          <div style={{ fontSize: 18, color: "#9ca3af" }}>
            {formatPrice(signal.current_price, pair)}
          </div>
        </div>
        <div style={{ flex: 1 }} />
        <ScoreGauge score={signal.total_score} label="総合スコア" size={110} />
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              fontSize: 28,
              fontWeight: 900,
              color: directionColor(signal.direction),
            }}
          >
            {directionLabel(signal.direction)}
          </div>
          <div
            style={{
              fontSize: 12,
              color: strengthColor(signal.strength),
              fontWeight: 600,
            }}
          >
            {scoreEmoji(signal.total_score)}{" "}
            {signal.strength === "STRONG"
              ? "強い候補"
              : signal.strength === "WATCH"
              ? "監視"
              : "無視"}
          </div>
        </div>
      </div>

      {/* Price chart */}
      <PriceChart pair={pair} liveTick={{ price: signal.current_price, score: signal.total_score }} />

      {/* Alerts */}
      {signal.alerts.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          {signal.alerts.map((a, i) => (
            <div
              key={i}
              style={{
                background: a.level === "danger" ? "#7f1d1d33" : "#78350f33",
                border: `1px solid ${a.level === "danger" ? "#ef444466" : "#f5970066"}`,
                borderRadius: 8,
                padding: "8px 12px",
                fontSize: 13,
                marginBottom: 6,
              }}
            >
              {a.message}
            </div>
          ))}
        </div>
      )}

      {/* Radar */}
      <Section title="スコア分析">
        <div style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "#9ca3af", fontSize: 11 }} />
              <Radar
                name="スコア"
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
              />
              <Tooltip
                contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                formatter={(v: number) => [`${v.toFixed(1)}%`, "スコア"]}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      {/* Technical */}
      <Section title="テクニカル分析 (60点)">
        <ScoreBar label="トレンド (EMA)" value={signal.technical.trend_score} max={20} detail={signal.technical.trend_detail} />
        <ScoreBar label="MACD" value={signal.technical.macd_score} max={15} detail={signal.technical.macd_detail} />
        <ScoreBar label="RSI" value={signal.technical.rsi_score} max={10} detail={signal.technical.rsi_detail} />
        <ScoreBar label="ボリンジャーバンド" value={signal.technical.bollinger_score} max={10} detail={signal.technical.bollinger_detail} />
        <ScoreBar label="ATR (ボラティリティ)" value={signal.technical.atr_score} max={5} detail={signal.technical.atr_detail} />
        <div style={{ textAlign: "right", fontSize: 13, color: "#9ca3af", marginTop: 4 }}>
          合計: <strong style={{ color: "#f3f4f6" }}>{signal.technical.total.toFixed(1)} / 60</strong>
        </div>
      </Section>

      {/* Fundamental */}
      <Section title="ファンダメンタル分析 (40点)">
        <ScoreBar label="金利差" value={signal.fundamental.interest_rate_score} max={15} detail={signal.fundamental.interest_rate_detail} />
        <ScoreBar label="中央銀行スタンス" value={signal.fundamental.central_bank_score} max={10} detail={signal.fundamental.central_bank_detail} />
        <ScoreBar label="経済指標" value={signal.fundamental.economic_score} max={10} detail={signal.fundamental.economic_detail} />
        <ScoreBar label="リスク環境" value={signal.fundamental.risk_score} max={5} detail={signal.fundamental.risk_detail} />
        <div style={{ textAlign: "right", fontSize: 13, color: "#9ca3af", marginTop: 4 }}>
          合計: <strong style={{ color: "#f3f4f6" }}>{signal.fundamental.total.toFixed(1)} / 40</strong>
        </div>
      </Section>

      {/* Checklist */}
      <Section title="判断根拠">
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {signal.checklist.map((item, i) => (
            <li key={i} style={{ fontSize: 13, color: "#d1d5db", marginBottom: 5, lineHeight: 1.4 }}>
              {item}
            </li>
          ))}
        </ul>
      </Section>

      <div style={{ fontSize: 11, color: "#4b5563", textAlign: "right", marginTop: 16 }}>
        更新: {new Date(signal.timestamp).toLocaleString("ja-JP")}
      </div>
    </div>
  );
};
