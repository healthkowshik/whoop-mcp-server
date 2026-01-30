from datetime import date, datetime

from pydantic import BaseModel, computed_field


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

    @computed_field
    @property
    def date(self) -> date:
        """Date of the sleep (based on end/wake time, falls back to start if ongoing)."""
        dt = self.end if self.end is not None else self.start
        return dt.date()

    @computed_field
    @property
    def weekday(self) -> str:
        """Day of week for the sleep (e.g., 'Monday', 'Tuesday'). Based on end/wake time, falls back to start if ongoing."""
        dt = self.end if self.end is not None else self.start
        return dt.strftime("%A")

    @computed_field
    @property
    def is_weekend(self) -> bool:
        """Whether the sleep falls on a weekend (Saturday or Sunday). Based on end/wake time, falls back to start if ongoing."""
        dt = self.end if self.end is not None else self.start
        return dt.weekday() >= 5
