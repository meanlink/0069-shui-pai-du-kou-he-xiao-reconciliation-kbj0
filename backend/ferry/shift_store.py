from fastapi import HTTPException

def list_shifts(cx):
    return cx.execute("""
        SELECT s.*,count(p.serial) AS scans
        FROM ferry_shifts s LEFT JOIN punch_events p ON s.code=p.shift_code
        GROUP BY s.code ORDER BY s.service_day DESC,s.departure_minute,s.code
    """).fetchall()

def get_shift(cx, code, *, lock=False):
    sql = "SELECT * FROM ferry_shifts WHERE code=%s"
    row = cx.execute(sql + (" FOR UPDATE" if lock else ""), (code,)).fetchone()
    if row is None:
        raise HTTPException(404, "班次号不存在")
    return row

def put_shift(cx, shift):
    return cx.execute("""
        INSERT INTO ferry_shifts(code,route,service_day,departure_minute,capacity)
        VALUES (%(code)s,%(route)s,%(service_day)s,%(departure_minute)s,%(capacity)s)
        RETURNING *
    """, shift.model_dump()).fetchone()
