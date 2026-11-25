from datetime import date
from pydantic import BaseModel, Field
from typing import Annotated

ShiftMinute = Annotated[int, Field(ge=0, le=2879)]

class Shift(BaseModel):
    code: str = Field(pattern=r"^F-[0-9]{3}$")
    route: str = Field(min_length=2, max_length=32)
    service_day: date
    departure_minute: ShiftMinute
    capacity: int = Field(gt=0, le=500)

def admission_window(departure_minute: int) -> tuple[int, int]:
    return max(0, departure_minute - 20), departure_minute + 3
