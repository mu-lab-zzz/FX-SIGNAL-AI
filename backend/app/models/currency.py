from pydantic import BaseModel
from typing import Dict, List, Optional


class CurrencyStrength(BaseModel):
    currency: str
    score: float  # -100 to +100
    stars: int    # 1-5
    trend: str    # "rising" | "falling" | "stable"
    vs_pairs: Dict[str, float] = {}


class CurrencyStrengthMap(BaseModel):
    generated_at: str
    strengths: List[CurrencyStrength]


class InterestRateData(BaseModel):
    currency: str
    central_bank: str
    current_rate: float
    previous_rate: float
    next_meeting: str
    trend: str  # "hawkish" | "dovish" | "neutral"


class CentralBankStance(BaseModel):
    bank: str
    currency: str
    stance: str   # "hawkish" | "dovish" | "neutral"
    confidence: float  # 0-1
    last_statement: str
    key_phrases: List[str]


class EconomicIndicator(BaseModel):
    name: str
    currency: str
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    impact: str   # "high" | "medium" | "low"
    surprise: float = 0.0  # actual - forecast
    scheduled_at: str
