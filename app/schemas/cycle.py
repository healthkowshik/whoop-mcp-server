from datetime import datetime

from pydantic import BaseModel, computed_field


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

    @computed_field
    @property
    def duration_hours(self) -> float | None:
        """Duration of the cycle in hours (rounded to 2 decimal places). Returns None if cycle hasn't ended."""
        if self.end is None:
            return None
        delta = self.end - self.start
        return round(delta.total_seconds() / 3600, 2)
