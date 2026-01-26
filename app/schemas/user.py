from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: int
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class BodyMeasurement(BaseModel):
    height_meter: float | None = None
    weight_kilogram: float | None = None
    max_heart_rate: int | None = None
