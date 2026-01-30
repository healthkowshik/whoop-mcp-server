from datetime import date, datetime

from pydantic import BaseModel, computed_field, field_serializer


class StageSummary(BaseModel):
    total_in_bed_time_milli: int | None = None
    total_awake_time_milli: int | None = None
    total_no_data_time_milli: int | None = None
    total_light_sleep_time_milli: int | None = None
    total_slow_wave_sleep_time_milli: int | None = None
    total_rem_sleep_time_milli: int | None = None
    sleep_cycle_count: int | None = None
    disturbance_count: int | None = None


class SleepScore(BaseModel):
    stage_summary: StageSummary | None = None
    sleep_needed: dict | None = None
    respiratory_rate: float | None = None
    sleep_performance_percentage: float | None = None
    sleep_consistency_percentage: float | None = None
    sleep_efficiency_percentage: float | None = None


class Sleep(BaseModel):
    id: str
    user_id: int
    start: datetime
    end: datetime | None = None
    timezone_offset: str | None = None
    nap: bool = False
    score_state: str
    score: SleepScore | None = None
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
        """Date of the sleep (based on end/wake time, falls back to start if ongoing)."""
        dt = self.end if self.end is not None else self.start
        return dt.date()

    @computed_field
    @property
    def weekday(self) -> str:
        """Day of week (e.g., 'Monday'). Based on end/wake time, falls back to start if ongoing."""
        dt = self.end if self.end is not None else self.start
        return dt.strftime("%A")

    @computed_field
    @property
    def is_weekend(self) -> bool:
        """Whether it falls on a weekend. Based on end/wake time, falls back to start if ongoing."""
        dt = self.end if self.end is not None else self.start
        return dt.weekday() >= 5
