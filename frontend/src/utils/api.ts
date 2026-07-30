const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

import type {
  FXSignal,
  RankingResponse,
  CurrencyStrengthMap,
  BacktestResult,
  NewsItem,
} from "../types";

export const api = {
  getSignal: (pair: string) =>
    fetchJson<FXSignal>(`/signals/${pair.replace("/", "-")}`),

  getRanking: () => fetchJson<RankingResponse>("/pairs/ranking"),

  getCurrencyStrength: () =>
    fetchJson<CurrencyStrengthMap>("/pairs/strength"),

  getBacktest: (pair: string, years = 5) =>
    fetchJson<BacktestResult>(`/backtest/${pair.replace("/", "-")}?years=${years}`),

  getNews: () =>
    fetchJson<{ items: NewsItem[] }>("/news/recent"),

  getOhlcv: (pair: string, timeframe = "D", count = 120) =>
    fetchJson<{ pair: string; timeframe: string; bars: OhlcvBar[] }>(
      `/prices/${pair.replace("/", "-")}?timeframe=${timeframe}&count=${count}`
    ),
};

export interface OhlcvBar {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
}
