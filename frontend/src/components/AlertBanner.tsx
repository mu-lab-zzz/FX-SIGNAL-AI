import React, { useEffect, useState } from "react";
import { WsAlert } from "../hooks/useWebSocket";

interface Props {
  alert: WsAlert | null;
}

export const AlertBanner: React.FC<Props> = ({ alert }) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (alert) {
      setVisible(true);
      const t = setTimeout(() => setVisible(false), 8000);
      return () => clearTimeout(t);
    }
  }, [alert]);

  if (!alert || !visible) return null;

  const isBuy = alert.direction === "BUY";

  return (
    <div
      style={{
        position: "fixed",
        top: 64,
        right: 16,
        zIndex: 200,
        background: isBuy ? "#14532d" : "#7f1d1d",
        border: `1px solid ${isBuy ? "#22c55e" : "#ef4444"}`,
        borderRadius: 12,
        padding: "14px 20px",
        maxWidth: 340,
        boxShadow: "0 8px 32px #00000066",
        animation: "slideIn 0.3s ease",
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 800, color: "#f3f4f6", marginBottom: 4 }}>
        🔔 シグナル通知
      </div>
      <div style={{ fontSize: 13, color: "#d1d5db" }}>{alert.message}</div>
      <button
        onClick={() => setVisible(false)}
        style={{
          position: "absolute",
          top: 8,
          right: 12,
          background: "none",
          border: "none",
          color: "#9ca3af",
          cursor: "pointer",
          fontSize: 16,
        }}
      >×</button>
    </div>
  );
};
