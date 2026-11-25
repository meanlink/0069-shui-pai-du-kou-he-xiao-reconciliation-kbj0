from fastapi import HTTPException

def get_pass(cx, code):
    row = cx.execute("SELECT * FROM ferry_passes WHERE code=%s", (code,)).fetchone()
    if not row:
        raise HTTPException(404, "月票号未登记")
    return row

def applies_to(holder, shift):
    return holder["route"] == shift["route"] and holder["starts"] <= shift["service_day"] <= holder["ends"]

def available_passes(cx):
    return cx.execute("SELECT * FROM ferry_passes ORDER BY code").fetchall()
