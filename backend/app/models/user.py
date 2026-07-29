from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UserCreate(BaseModel):
    email: str
    password: str
    display_name: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    alert_pairs: List[str] = []
    alert_min_score: float = 80.0


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AlertSettings(BaseModel):
    pairs: List[str] = []
    min_score: float = 80.0
