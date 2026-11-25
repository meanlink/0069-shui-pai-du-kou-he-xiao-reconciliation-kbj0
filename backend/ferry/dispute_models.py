from typing import Literal
from pydantic import BaseModel, Field

class Appeal(BaseModel):
    serial: str = Field(pattern=r"^[A-Z0-9-]{3,24}$")
    operator_note: str = Field(min_length=4, max_length=240)

class Decision(BaseModel):
    ruling: Literal["count", "reject"]
    resolution: str = Field(min_length=4, max_length=240)
