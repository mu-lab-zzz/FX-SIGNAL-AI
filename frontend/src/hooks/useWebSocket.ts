import { useEffect, useRef, useCallback, useState } from "react";

export interface WsTick {
  pair: string;
  price: number;
  change_pct: number;
  score: number;
  direction: string;
  strength: string;
  ts: string;
}

export interface WsAlert {
  type: "alert";
  pair: string;
  score: number;
  direction: string;
  message: string;
}

type WsMessage =
  | { type: "batch"; ticks: WsTick[] }
  | WsAlert;

const WS_URL =
  (process.env.REACT_APP_WS_URL || "ws://localhost:8000") + "/ws/prices";

const RECONNECT_DELAY_MS = 3000;

export function useWebSocket(onTicks: (ticks: WsTick[]) => void, onAlert?: (a: WsAlert) => void) {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const onTicksRef = useRef(onTicks);
  const onAlertRef = useRef(onAlert);
  onTicksRef.current = onTicks;
  onAlertRef.current = onAlert;

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => setConnected(true);

    socket.onmessage = (ev) => {
      try {
        const msg: WsMessage = JSON.parse(ev.data);
        if (msg.type === "batch") {
          onTicksRef.current(msg.ticks);
        } else if (msg.type === "alert") {
          onAlertRef.current?.(msg);
        }
      } catch {}
    };

    socket.onclose = () => {
      setConnected(false);
      setTimeout(connect, RECONNECT_DELAY_MS);
    };

    socket.onerror = () => socket.close();
  }, []);

  useEffect(() => {
    connect();
    const ping = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send("ping");
      }
    }, 20_000);
    return () => {
      clearInterval(ping);
      ws.current?.close();
    };
  }, [connect]);

  return { connected };
}
