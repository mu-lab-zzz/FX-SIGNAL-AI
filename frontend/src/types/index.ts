export type SignalDirection = "BUY" | "SELL" | "NEUTRAL";
export type SignalStrength = "STRONG" | "WATCH" | "IGNORE";

export interface TechnicalScoreDetail {
  trend_score: number;
  macd_score: number;
  rsi_score: number;
  bollinger_score: number;
  atr_score: number;
  total: number;
  trend_detail: string;
  macd_detail: string;
  rsi_detail: string;
  bollinger_detail: string;
  atr_detail: string;
}

export interface FundamentalScoreDetail {
  interest_rate_score: number;
  central_bank_score: number;
  economic_score: number;
  risk_score: number;
  total: number;
  interest_rate_detail: string;
  central_bank_detail: string;
  economic_detail: string;
  risk_detail: string;
}

export interface AlertItem {
  level: string;
  message: string;
}

export interface FXSignal {
  pair: string;
  timestamp: string;
  current_price: number;
  direction: SignalDirection;
  strength: SignalStrength;
  total_score: number;
  technical: TechnicalScoreDetail;
  fundamental: FundamentalScoreDetail;
  checklist: string[];
  alerts: AlertItem[];
  summary: string;
}

export interface PairRanking {
  rank: number;
  pair: string;
  score: number;
  direction: SignalDirection;
  strength: SignalStrength;
  change_24h: number;
  summary: string;
}

export interface RankingResponse {
  generated_at: string;
  rankings: PairRanking[];
}

export interface CurrencyStrength {
  currency: string;
  score: number;
  stars: number;
  trend: string;
}

export interface CurrencyStrengthMap {
  generated_at: string;
  strengths: CurrencyStrength[];
}

export interface NewsItem {
  headline: string;
  source: string;
  published: string;
  currency_impact: Record<string, number>;
  classification: string;
  summary: string;
}

export interface BacktestResult {
  pair: string;
  start_date: string;
  end_date: string;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_profit_pips: number;
  avg_loss_pips: number;
  profit_factor: number;
  max_consecutive_losses: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  total_return_pct: number;
  trades: Trade[];
}

export interface Trade {
  pair: string;
  entry_price: number;
  exit_price: number;
  direction: string;
  entry_date: string;
  exit_date: string;
  pips: number;
  return_pct: number;
}
