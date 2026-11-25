from fastapi import HTTPException

def hold_day(cx, service_day):
    cx.execute("SELECT pg_advisory_xact_lock(1939,%s)", (service_day.toordinal(),))

def require_open_day(cx, service_day):
    hold_day(cx, service_day)
    if cx.execute("SELECT 1 FROM ferry_closes WHERE service_day=%s", (service_day,)).fetchone():
        raise HTTPException(409, "营业日已封账")
