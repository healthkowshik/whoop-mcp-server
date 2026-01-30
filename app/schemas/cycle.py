from datetime import date, datetime

from pydantic import BaseModel, computed_field, field_serializer


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

    @field_serializer("start", "end", "created_at", "updated_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """Format datetime with timezone offset for display."""
        if value is None:
            return None
        if self.timezone_offset:
            return f"{value.strftime('%Y-%m-%d %I:%M %p')} ({self.timezone_offset})"
        return value.isoformat()

    @computed_field
    @property
    def duration_hours(self) -> float | None:
        """Duration of the cycle in hours (rounded to 2 decimal places)."""
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
        """Day of week (e.g., 'Monday'). Based on end time, falls back to start if ongoing."""
        dt = self.end if self.end is not None else self.start
        return dt.strftime("%A")

    @computed_field
    @property
    def is_weekend(self) -> bool:
        """Whether it falls on a weekend. Based on end time, falls back to start if ongoing."""
        dt = self.end if self.end is not None else self.start
        return dt.weekday() >= 5
