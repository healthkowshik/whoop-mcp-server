from datetime import date, datetime

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

    @computed_field
    @property
    def date(self) -> date:
        """Date of the cycle (based on end time, falls back to start if ongoing)."""
        dt = self.end if self.end is not None else self.start
        return dt.date()

    @computed_field
    @property
    def weekday(self) -> str:
        """Day of week for the cycle (e.g., 'Monday', 'Tuesday'). Based on end time, falls back to start if ongoing."""
        dt = self.end if self.end is not None else self.start
        return dt.strftime("%A")

    @computed_field
    @property
    def is_weekend(self) -> bool:
        """Whether the cycle falls on a weekend (Saturday or Sunday). Based on end time, falls back to start if ongoing."""
        dt = self.end if self.end is not None else self.start
        return dt.weekday() >= 5
