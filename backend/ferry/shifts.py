from fastapi import APIRouter, Depends
from core import db, require
from ferry.day_lock import require_open_day
from ferry.shift_models import Shift
from ferry.shift_store import list_shifts, put_shift

router = APIRouter(prefix="/api/ferry")

@router.get("/shifts")
def shifts(_=Depends(require())):
    with db() as cx:
        return list_shifts(cx)

@router.post("/shifts", status_code=201)
def add_shift(shift: Shift, _=Depends(require("operator"))):
    with db() as cx:
        require_open_day(cx, shift.service_day)
        return put_shift(cx, shift)
