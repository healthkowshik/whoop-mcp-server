from datetime import datetime

from pydantic import BaseModel


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
