from fastapi import HTTPException
from ferry.day_lock import require_open_day
from ferry.passbook import applies_to, get_pass
from ferry.punch_store import insert_punch, previous_first, punch_by_serial
from ferry.shift_models import admission_window
from ferry.shift_store import get_shift

def register(cx, punch):
    shift = get_shift(cx, punch.shift_code)
    require_open_day(cx, shift["service_day"])
    existing = punch_by_serial(cx, punch.serial)
    if existing:
        if all(existing[key] == value for key, value in punch.model_dump().items()):
            return existing
        raise HTTPException(409, "闸机流水号已对应另一笔原始刷卡")
    holder = get_pass(cx, punch.pass_code)
    start, end = admission_window(shift["departure_minute"])
    if not applies_to(holder, shift):
        verdict = "ineligible"
    elif not start <= punch.minute <= end:
        verdict = "outside"
    else:
        verdict = "repeat" if previous_first(cx, punch.shift_code, punch.pass_code) else "first"
    return insert_punch(cx, punch, verdict)
