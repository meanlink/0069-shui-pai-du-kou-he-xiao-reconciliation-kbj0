def list_punches(cx):
    return cx.execute("""
        SELECT p.*,s.route,s.service_day
        FROM punch_events p JOIN ferry_shifts s ON s.code=p.shift_code
        ORDER BY s.service_day DESC,p.minute,p.serial
    """).fetchall()

def previous_first(cx, shift_code, pass_code):
    return cx.execute("""
        SELECT serial,minute FROM punch_events
        WHERE shift_code=%s AND pass_code=%s AND verdict='first'
    """, (shift_code, pass_code)).fetchone()

def punch_by_serial(cx, serial):
    return cx.execute("SELECT * FROM punch_events WHERE serial=%s", (serial,)).fetchone()

def insert_punch(cx, punch, verdict):
    return cx.execute("""
        INSERT INTO punch_events(serial,shift_code,pass_code,gate,minute,verdict)
        VALUES (%(serial)s,%(shift_code)s,%(pass_code)s,%(gate)s,%(minute)s,%(verdict)s)
        RETURNING *
    """, punch.model_dump() | {"verdict": verdict}).fetchone()
