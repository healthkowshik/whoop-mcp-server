from datetime import datetime

from pydantic import BaseModel


class CycleScore(BaseModel):
    strain: float | None = None
    kilojoule: float | None = None
    average_heart_rate: int | None = None
    max_heart_rate: int | None = None


class Cycle(BaseModel):
    id: int
    user_id: int
    start: datetime
    end: datetime | None = None
    timezone_offset: str | None = None
    score_state: str
    score: CycleScore | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
