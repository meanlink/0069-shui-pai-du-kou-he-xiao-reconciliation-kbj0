def get_disputes(cx):
    return cx.execute("""
        SELECT d.*,p.shift_code,p.pass_code,p.verdict,p.minute
        FROM shift_disputes d JOIN punch_events p ON p.serial=d.serial
        ORDER BY (d.ruling='open') DESC,d.serial
    """).fetchall()

def insert_dispute(cx, appeal):
    return cx.execute("""
        INSERT INTO shift_disputes(serial,operator_note)
        VALUES (%(serial)s,%(operator_note)s) RETURNING *
    """, appeal.model_dump()).fetchone()

def has_counted_appeal(cx, pass_code, shift_code):
    return cx.execute("""
        SELECT 1 FROM shift_disputes d JOIN punch_events p ON d.serial=p.serial
        WHERE p.pass_code=%s AND p.shift_code=%s AND d.ruling='count'
    """, (pass_code,shift_code)).fetchone() is not None

def resolve_dispute(cx, serial, decision):
    return cx.execute("""
        UPDATE shift_disputes SET ruling=%s,resolution=%s,amount=%s
        WHERE serial=%s AND ruling='open' RETURNING *
    """, (decision.ruling, decision.resolution, int(decision.ruling == "count"), serial)).fetchone()
