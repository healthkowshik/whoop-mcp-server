from datetime import datetime

from pydantic import BaseModel


class RecoveryScore(BaseModel):
    user_calibrating: bool | None = None
    recovery_score: float | None = None
    resting_heart_rate: float | None = None
    hrv_rmssd_milli: float | None = None
    spo2_percentage: float | None = None
    skin_temp_celsius: float | None = None


class Recovery(BaseModel):
    cycle_id: int
    sleep_id: str
    user_id: int
    score_state: str
    score: RecoveryScore | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
