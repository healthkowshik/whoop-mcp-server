from datetime import datetime

from pydantic import BaseModel


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
