from typing import Literal
from pydantic import BaseModel, Field
from ferry.shift_models import ShiftMinute

class Punch(BaseModel):
    serial: str = Field(pattern=r"^[A-Z0-9-]{3,24}$")
    shift_code: str = Field(pattern=r"^F-[0-9]{3}$")
    pass_code: str = Field(pattern=r"^M-[0-9]{3}$")
    minute: ShiftMinute
    gate: Literal["east", "west"]
