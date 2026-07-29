import React, { useEffect, useState } from "react";
import type { NewsItem } from "../types";
import { api } from "../utils/api";

const impactBadge = (score: number): React.ReactNode => {
  const color = score > 0 ? "#22c55e" : score < 0 ? "#ef4444" : "#6b7280";
  const label = score > 0 ? `+${score} 強気` : score < 0 ? `${score} 弱気` : "中立";
  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 700,
        color,
        background: `${color}22`,
        borderRadius: 4,
        padding: "1px 5px",
        marginLeft: 4,
      }}
    >
      {label}
    </span>
  );
};

export const NewsPanel: React.FC = () => {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getNews()
      .then((data) => setItems(data.items))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color: "#9ca3af", padding: 20 }}>ニュース取得中...</div>;

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 700, color: "#f3f4f6", marginBottom: 16 }}>
        AIニュース解析
      </div>
      {items.map((item, i) => (
        <div
          key={i}
          style={{
            background: "#1f2937",
            borderRadius: 10,
            padding: 14,
            marginBottom: 10,
          }}
        >
          <div style={{ fontSize: 13, color: "#f3f4f6", lineHeight: 1.5, marginBottom: 6 }}>
            {item.summary || item.headline}
          </div>
          <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 6 }}>
            {item.source} · {new Date(item.published).toLocaleDateString("ja-JP")}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {Object.entries(item.currency_impact).map(([ccy, score]) => (
              <div key={ccy} style={{ display: "flex", alignItems: "center" }}>
                <span style={{ fontSize: 11, color: "#9ca3af", fontWeight: 700 }}>{ccy}</span>
                {impactBadge(score as number)}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
