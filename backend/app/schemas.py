from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ---------- User ----------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime


# ---------- Session ----------
class SessionCreate(BaseModel):
    title: str | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thread_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime


# ---------- Message ----------
class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    agent: str | None
    content: str
    created_at: datetime
# ---------- DailyLog ----------
class DailyLogCreate(BaseModel):
    log_date: datetime
    trained: bool = False
    training_note: str | None = None
    diet_note: str | None = None
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    mood: str | None = None
    note: str | None = None


class DailyLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    log_date: datetime
    trained: bool
    training_note: str | None
    diet_note: str | None
    sleep_hours: float | None
    mood: str | None
    note: str | None
    created_at: datetime


# ---------- Weight ----------
class WeightCreate(BaseModel):
    record_date: datetime
    weight_kg: float = Field(gt=0, lt=500)
    note: str | None = None


class WeightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_date: datetime
    weight_kg: float
    note: str | None
    created_at: datetime


class WeightTrendPoint(BaseModel):
    record_date: datetime
    weight_kg: float

# ---------- Plan ----------
class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    kind: str
    content: dict
    summary: str | None
    created_at: datetime


class SessionWithPreview(SessionOut):
    last_message: str | None = None