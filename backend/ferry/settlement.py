from fastapi import HTTPException
from ferry.close_store import day_records, freeze, get_close
from ferry.day_lock import hold_day, require_open_day
from ferry.pivot import pivot

def summary(cx, day):
    hold_day(cx, day)
    receipt = get_close(cx, day)
    if receipt:
        return {"rows": receipt["rows"], "closed": True, "reviewer": receipt["closed_by"]}
    return {"rows": pivot(*day_records(cx, day)), "closed": False}

def close(cx, day, reviewer):
    require_open_day(cx, day)
    rows = pivot(*day_records(cx, day))
    if not rows:
        raise HTTPException(404, "营业日没有运营班次")
    if any(row["pending"] for row in rows):
        raise HTTPException(409, "存在待签审的核销复核单")
    if any(row["riders"] > row["seat_limit"] for row in rows):
        raise HTTPException(409, "有班次的有效核销超过核定载客数")
    return freeze(cx, day, rows, reviewer)
