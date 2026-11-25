from psycopg.types.json import Jsonb

def day_records(cx, day):
    shifts = cx.execute("""
        SELECT * FROM ferry_shifts WHERE service_day=%s ORDER BY departure_minute,code
    """, (day,)).fetchall()
    scans = cx.execute("""
        SELECT p.*,d.ruling FROM punch_events p
        JOIN ferry_shifts s ON s.code=p.shift_code LEFT JOIN shift_disputes d ON d.serial=p.serial
        WHERE s.service_day=%s ORDER BY p.minute,p.serial
    """, (day,)).fetchall()
    return shifts, scans

def freeze(cx, day, rows, reviewer):
    return cx.execute("""
        INSERT INTO ferry_closes(service_day,rows,closed_by) VALUES (%s,%s,%s) RETURNING *
    """, (day,Jsonb(rows),reviewer)).fetchone()

def get_close(cx, day):
    return cx.execute("SELECT * FROM ferry_closes WHERE service_day=%s", (day,)).fetchone()
