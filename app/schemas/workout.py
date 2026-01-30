from datetime import date, datetime

from pydantic import BaseModel, computed_field, field_serializer


class ZoneDuration(BaseModel):
    zone_zero_milli: int | None = None
    zone_one_milli: int | None = None
    zone_two_milli: int | None = None
    zone_three_milli: int | None = None
    zone_four_milli: int | None = None
    zone_five_milli: int | None = None


class WorkoutScore(BaseModel):
    strain: float | None = None
    average_heart_rate: int | None = None
    max_heart_rate: int | None = None
    kilojoule: float | None = None
    percent_recorded: float | None = None
    distance_meter: float | None = None
    altitude_gain_meter: float | None = None
    altitude_change_meter: float | None = None
    zone_duration: ZoneDuration | None = None


class Workout(BaseModel):
    id: str
    user_id: int
    start: datetime
    end: datetime | None = None
    timezone_offset: str | None = None
    sport_id: int
    score_state: str
    score: WorkoutScore | None = None
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
    def date(self) -> date:
        """Date of the workout (based on end time, falls back to start if ongoing)."""
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
