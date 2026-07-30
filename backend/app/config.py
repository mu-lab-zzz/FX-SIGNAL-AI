from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "FX Signal AI"
    debug: bool = False

    # Data providers
    oanda_api_key: str = ""
    oanda_account_id: str = ""
    alpha_vantage_api_key: str = ""
    twelve_data_api_key: str = ""

    # Auth
    jwt_secret: str = "change-me-in-production"

    # AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # News
    newsapi_key: str = ""       # https://newsapi.org (free: 100 req/day)

    # Economic calendar
    trading_economics_api_key: str = ""

    # CORS (comma-separated origins, "*" = allow all)
    cors_origins: str = "*"

    # Scoring thresholds
    strong_buy_threshold: int = 80
    watch_threshold: int = 65

    # Supported pairs
    fx_pairs: List[str] = [
        "USD/JPY", "EUR/USD", "GBP/USD",
        "AUD/JPY", "EUR/JPY", "NZD/JPY",
        "AUD/USD", "GBP/JPY", "USD/CHF",
    ]

    # Supported currencies for strength map
    currencies: List[str] = ["USD", "JPY", "EUR", "GBP", "AUD", "NZD", "CHF", "CAD"]

    class Config:
        env_file = ".env"


settings = Settings()
