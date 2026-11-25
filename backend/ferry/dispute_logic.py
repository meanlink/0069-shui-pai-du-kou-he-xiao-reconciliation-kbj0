from fastapi import HTTPException
from ferry.day_lock import require_open_day
from ferry.dispute_store import insert_dispute, has_counted_appeal, resolve_dispute
from ferry.passbook import applies_to, get_pass
from ferry.punch_store import previous_first, punch_by_serial
from ferry.shift_store import get_shift

def context(cx, serial):
    punch = punch_by_serial(cx, serial)
    if not punch:
        raise HTTPException(404, "流水号不存在")
    shift = get_shift(cx, punch["shift_code"])
    require_open_day(cx, shift["service_day"])
    return punch, shift

def open_ticket(cx, appeal):
    punch, _ = context(cx, appeal.serial)
    if punch["verdict"] not in ("outside", "ineligible"):
        raise HTTPException(409, "有效或重复核销不进入班次复核")
    return insert_dispute(cx, appeal)

def adjudicate(cx, serial, decision):
    punch, shift = context(cx, serial)
    holder = get_pass(cx, punch["pass_code"])
    if decision.ruling == "count" and (
        not applies_to(holder, shift)
        or previous_first(cx, shift["code"], holder["code"])
        or has_counted_appeal(cx, holder["code"], shift["code"])
    ):
        raise HTTPException(409, "该月票不适用该班次，或已经计入该班次")
    row = resolve_dispute(cx, serial, decision)
    if row is None:
        raise HTTPException(409, "只允许签审待处理的复核单")
    return row
