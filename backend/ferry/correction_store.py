"""Persistence for post-close shift corrections (改记/更正单) and their +/- entries."""

def correction_by_serial(cx, serial):
    return cx.execute(
        "SELECT * FROM ferry_corrections WHERE serial=%s", (serial,)
    ).fetchone()

def correction_by_original(cx, original_serial):
    return cx.execute(
        "SELECT * FROM ferry_corrections WHERE original_serial=%s", (original_serial,)
    ).fetchone()

def get_correction_any(cx, serial):
    """Fetch by correction serial or by the original gate serial."""
    return cx.execute(
        "SELECT * FROM ferry_corrections WHERE serial=%s OR original_serial=%s",
        (serial, serial),
    ).fetchone()

def list_corrections(cx, day=None, *, serial=None, original_serial=None, pass_code=None):
    clauses, params = [], []
    if day is not None:
        clauses.append("service_day=%s"); params.append(day)
    if serial is not None:
        clauses.append("serial=%s"); params.append(serial)
    if original_serial is not None:
        clauses.append("original_serial=%s"); params.append(original_serial)
    if pass_code is not None:
        clauses.append("pass_code=%s"); params.append(pass_code)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return cx.execute(
        f"SELECT * FROM ferry_corrections{where} ORDER BY id DESC", params
    ).fetchall()

def adjustments_for_correction(cx, serial):
    return cx.execute(
        "SELECT * FROM ferry_adjustments WHERE correction_serial=%s ORDER BY id", (serial,)
    ).fetchall()

def adjustments_for_day(cx, day):
    return cx.execute(
        "SELECT * FROM ferry_adjustments WHERE service_day=%s ORDER BY id", (day,)
    ).fetchall()

def list_adjustments(cx, day=None):
    if day is None:
        return cx.execute("SELECT * FROM ferry_adjustments ORDER BY id DESC").fetchall()
    return adjustments_for_day(cx, day)

def adjustments_for_shift(cx, shift_code):
    return cx.execute(
        "SELECT * FROM ferry_adjustments WHERE shift_code=%s ORDER BY id", (shift_code,)
    ).fetchall()

def counted_passes(cx, shift_code):
    """Base counted set, mirroring pivot.accepted: verdict first OR a count ruling."""
    return {row["pass_code"] for row in cx.execute(
        """
        SELECT DISTINCT p.pass_code
        FROM punch_events p
        LEFT JOIN shift_disputes d ON d.serial = p.serial
        WHERE p.shift_code = %s
          AND (p.verdict = 'first' OR d.ruling = 'count')
        """,
        (shift_code,),
    ).fetchall()}

def insert_correction(cx, *, serial, original_serial, pass_code, wrong_shift_code,
                      shift_code, service_day, action, note, reviewer):
    return cx.execute(
        """
        INSERT INTO ferry_corrections
            (serial, original_serial, pass_code, wrong_shift_code, shift_code,
             service_day, action, note, created_by)
        VALUES (%(serial)s,%(original_serial)s,%(pass_code)s,%(wrong_shift_code)s,
                %(shift_code)s,%(service_day)s,%(action)s,%(note)s,%(reviewer)s)
        RETURNING *
        """,
        {
            "serial": serial, "original_serial": original_serial, "pass_code": pass_code,
            "wrong_shift_code": wrong_shift_code, "shift_code": shift_code,
            "service_day": service_day, "action": action, "note": note,
            "reviewer": reviewer,
        },
    ).fetchone()

def insert_adjustment(cx, *, correction_serial, service_day, shift_code,
                      pass_code, original_serial, kind, delta):
    return cx.execute(
        """
        INSERT INTO ferry_adjustments
            (correction_serial, service_day, shift_code, pass_code,
             original_serial, kind, delta)
        VALUES (%(correction_serial)s,%(service_day)s,%(shift_code)s,%(pass_code)s,
                %(original_serial)s,%(kind)s,%(delta)s)
        RETURNING *
        """,
        {
            "correction_serial": correction_serial, "service_day": service_day,
            "shift_code": shift_code, "pass_code": pass_code,
            "original_serial": original_serial, "kind": kind, "delta": delta,
        },
    ).fetchone()
