import React, { useEffect, useState } from "react";
import {
  ComposedChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
} from "recharts";
import { api, OhlcvBar } from "../utils/api";
import { formatPrice } from "../utils/format";

interface Props {
  pair: string;
  liveTick?: { price: number; score: number } | null;
}

type TF = "D" | "H4" | "H1";
const TF_LABELS: Record<TF, string> = { D: "日足", H4: "4時間", H1: "1時間" };

const CustomTooltip = ({ active, payload, pair }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload as OhlcvBar & { ema20: number; ema50: number };
  return (
    <div style={{
      background: "#0f172a", border: "1px solid #374151",
      borderRadius: 8, padding: "10px 14px", fontSize: 12,
    }}>
      <div style={{ color: "#9ca3af", marginBottom: 4 }}>{d.t?.slice(0, 10)}</div>
      <div style={{ color: "#f3f4f6" }}>
        O: {formatPrice(d.o, pair)} &nbsp;
        H: {formatPrice(d.h, pair)} &nbsp;
        L: {formatPrice(d.l, pair)} &nbsp;
        C: <strong style={{ color: d.c >= d.o ? "#22c55e" : "#ef4444" }}>
          {formatPrice(d.c, pair)}
        </strong>
      </div>
      {d.ema20 && (
        <div style={{ marginTop: 4 }}>
          <span style={{ color: "#60a5fa" }}>EMA20: {formatPrice(d.ema20, pair)}</span>
          &nbsp;&nbsp;
          <span style={{ color: "#f59e0b" }}>EMA50: {formatPrice(d.ema50, pair)}</span>
        </div>
      )}
    </div>
  );
};

function calcEma(data: OhlcvBar[], period: number): number[] {
  const k = 2 / (period + 1);
  const result: number[] = [];
  let prev = data[0]?.c ?? 0;
  for (const bar of data) {
    const ema = bar.c * k + prev * (1 - k);
    result.push(ema);
    prev = ema;
  }
  return result;
}

export const PriceChart: React.FC<Props> = ({ pair, liveTick }) => {
  const [bars, setBars]     = useState<(OhlcvBar & { ema20: number; ema50: number })[]>([]);
  const [tf, setTf]         = useState<TF>("D");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getOhlcv(pair, tf, tf === "D" ? 120 : 200)
      .then(({ bars: raw }) => {
        const ema20 = calcEma(raw, 20);
        const ema50 = calcEma(raw, 50);
        setBars(raw.map((b, i) => ({ ...b, ema20: ema20[i], ema50: ema50[i] })));
      })
      .catch(() => setBars([]))
      .finally(() => setLoading(false));
  }, [pair, tf]);

  const lastClose = liveTick?.price ?? bars[bars.length - 1]?.c;
  const priceColor = lastClose && bars.length > 1
    ? (lastClose >= bars[bars.length - 2]?.c ? "#22c55e" : "#ef4444")
    : "#9ca3af";

  const prices = bars.map((b) => b.c);
  const minP = Math.min(...prices) * 0.9995;
  const maxP = Math.max(...prices) * 1.0005;

  if (loading) return (
    <div style={{ height: 260, display: "flex", alignItems: "center",
      justifyContent: "center", color: "#6b7280", fontSize: 13 }}>
      チャート読み込み中...
    </div>
  );

  return (
    <div style={{ marginBottom: 24 }}>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: "#f3f4f6", flex: 1 }}>
          価格チャート
          {lastClose && (
            <span style={{ marginLeft: 10, color: priceColor, fontSize: 15 }}>
              {formatPrice(lastClose, pair)}
            </span>
          )}
        </div>
        {/* EMA legend */}
        <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#9ca3af" }}>
          <span><span style={{ color: "#60a5fa" }}>■</span> EMA20</span>
          <span><span style={{ color: "#f59e0b" }}>■</span> EMA50</span>
        </div>
        {/* Timeframe selector */}
        <div style={{ display: "flex", gap: 4 }}>
          {(["D", "H4", "H1"] as TF[]).map((t) => (
            <button key={t} onClick={() => setTf(t)} style={{
              background: tf === t ? "#1d4ed8" : "#374151",
              color: tf === t ? "#fff" : "#9ca3af",
              border: "none", borderRadius: 6,
              padding: "3px 8px", fontSize: 11, cursor: "pointer",
            }}>
              {TF_LABELS[t]}
            </button>
          ))}
        </div>
      </div>

      {/* Price chart */}
      <div style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={bars} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#1f2937" strokeDasharray="2 4" vertical={false} />
            <XAxis
              dataKey="t"
              tickFormatter={(v) => v?.slice(5, 10) ?? ""}
              tick={{ fill: "#6b7280", fontSize: 10 }}
              axisLine={false} tickLine={false}
              interval={Math.floor(bars.length / 6)}
            />
            <YAxis
              domain={[minP, maxP]}
              tick={{ fill: "#6b7280", fontSize: 10 }}
              axisLine={false} tickLine={false}
              width={58}
              tickFormatter={(v) => formatPrice(v, pair)}
            />
            <Tooltip content={<CustomTooltip pair={pair} />} />

            {/* Close price area */}
            <Area
              type="monotone" dataKey="c"
              stroke={priceColor} fill={`${priceColor}18`}
              strokeWidth={1.5} dot={false}
            />
            {/* EMA20 */}
            <Area
              type="monotone" dataKey="ema20"
              stroke="#60a5fa" fill="none"
              strokeWidth={1} dot={false} strokeDasharray="0"
            />
            {/* EMA50 */}
            <Area
              type="monotone" dataKey="ema50"
              stroke="#f59e0b" fill="none"
              strokeWidth={1} dot={false}
            />
            {/* Live price reference */}
            {liveTick?.price && (
              <ReferenceLine y={liveTick.price} stroke={priceColor}
                strokeDasharray="4 4" strokeWidth={1} />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Volume chart */}
      <div style={{ height: 48, marginTop: 2 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={bars} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <YAxis hide />
            <Bar dataKey="v" fill="#374151" radius={[1, 1, 0, 0]} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
