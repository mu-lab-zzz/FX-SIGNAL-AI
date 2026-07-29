from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


class SignalStrength(str, Enum):
    STRONG = "STRONG"      # 80+
    WATCH = "WATCH"        # 65-79
    IGNORE = "IGNORE"      # <65


class TechnicalScoreDetail(BaseModel):
    trend_score: float = Field(0, ge=0, le=20, description="EMA trend score")
    macd_score: float = Field(0, ge=0, le=15, description="MACD score")
    rsi_score: float = Field(0, ge=0, le=10, description="RSI score")
    bollinger_score: float = Field(0, ge=0, le=10, description="Bollinger Bands score")
    atr_score: float = Field(0, ge=0, le=5, description="ATR volatility score")
    total: float = Field(0, ge=0, le=60)

    trend_detail: str = ""
    macd_detail: str = ""
    rsi_detail: str = ""
    bollinger_detail: str = ""
    atr_detail: str = ""


class FundamentalScoreDetail(BaseModel):
    interest_rate_score: float = Field(0, ge=0, le=15, description="Interest rate differential")
    central_bank_score: float = Field(0, ge=0, le=10, description="Central bank stance")
    economic_score: float = Field(0, ge=0, le=10, description="Economic indicators")
    risk_score: float = Field(0, ge=0, le=5, description="Risk environment")
    total: float = Field(0, ge=0, le=40)

    interest_rate_detail: str = ""
    central_bank_detail: str = ""
    economic_detail: str = ""
    risk_detail: str = ""


class AlertItem(BaseModel):
    level: str  # "warning" | "info" | "danger"
    message: str


class FXSignal(BaseModel):
    pair: str
    timestamp: datetime
    current_price: float
    direction: SignalDirection
    strength: SignalStrength
    total_score: float = Field(ge=0, le=100)
    technical: TechnicalScoreDetail
    fundamental: FundamentalScoreDetail
    checklist: List[str] = []
    alerts: List[AlertItem] = []
    summary: str = ""

    @property
    def score_label(self) -> str:
        if self.total_score >= 80:
            return "🟢 強い買い候補" if self.direction == SignalDirection.BUY else "🔴 強い売り候補"
        elif self.total_score >= 65:
            return "🟡 監視"
        return "⚪ 無視"


class PairRanking(BaseModel):
    rank: int
    pair: str
    score: float
    direction: SignalDirection
    strength: SignalStrength
    change_24h: float = 0.0
    summary: str = ""


class RankingResponse(BaseModel):
    generated_at: datetime
    rankings: List[PairRanking]


class ExitSignal(BaseModel):
    pair: str
    direction: str
    triggered: bool
    reason: str
    severity: str  # "warning" | "danger"
