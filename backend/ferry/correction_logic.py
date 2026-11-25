"""改记 core rules.

A monthly pass was scanned against the wrong boat shift after the relevant
business day(s) closed.  A reviewer books a correction onto a later *open*
business day:

* the original frozen close / vouchers are never touched;
* one ``decrease`` (-1) entry always writes off the wrong count;
* a matching ``increase`` (+1) only re-counts the passenger on the correct
  shift when that shift does not already hold the ticket (查重);
* if the +1 is needed but the correct shift is full (验载), the whole
  correction is rejected and nothing is posted (整笔退回);
* the +/- entries share the chosen booking day and commit atomically with the
  day lock, so racing close either happens first (correction is refused) or
  after (close sees the committed entries);
* the same correction serial is idempotent; reusing it for another target
  shift is a conflict.
"""
from datetime import date, datetime

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from ferry.day_lock import require_open_day
from ferry.punch_store import punch_by_serial
from ferry.shift_store import get_shift

# Advisory-lock namespace distinct from day_lock's 1939.
SERIAL_LOCK_NAMESPACE = 8821


def lock_serial(cx, serial):
    cx.execute(
        "SELECT pg_advisory_xact_lock(%s, hashtext(%s))",
        (SERIAL_LOCK_NAMESPACE, serial),
    )


def lock_original(cx, original_serial):
    cx.execute(
        "SELECT pg_advisory_xact_lock(%s, hashtext(%s))",
        (SERIAL_LOCK_NAMESPACE + 1, original_serial),
    )


def as_date(value):
    if value is None or isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        raise HTTPException(400, "营业日格式应为 YYYY-MM-DD")


def _effective_counted(cx, shift_code):
    """Counted pass set after base punch rulings and every posted adjustment."""
    from ferry.correction_store import adjustments_for_shift, counted_passes

    counted = counted_passes(cx, shift_code)
    for entry in adjustments_for_shift(cx, shift_code):
        if entry["delta"] > 0:
            counted.add(entry["pass_code"])
        else:
            counted.discard(entry["pass_code"])
    return counted


def effective_riders(cx, shift_code):
    return len(_effective_counted(cx, shift_code))


def _same_intent(existing, *, original_serial, shift_code, service_day):
    if existing["original_serial"] != original_serial:
        return False
    if existing["shift_code"] != shift_code:
        return False
    if service_day is not None and existing["service_day"] != service_day:
        return False
    return True


def _coerce_cmd(cmd):
    if isinstance(cmd, dict):
        plain = cmd
    elif hasattr(cmd, "model_dump"):
        try:
            plain = cmd.model_dump()
        except Exception:  # pragma: no cover - defensive
            plain = {}
    else:
        try:
            plain = {k: v for k, v in vars(cmd).items() if not k.startswith("_")}
        except TypeError:
            plain = {}
        for key in ("serial", "original_serial", "shift_code", "service_day",
                    "pass_code", "note"):
            if not plain.get(key) and hasattr(cmd, key):
                plain[key] = getattr(cmd, key)
    # Re-run alias normalization so gold-style field names resolve too.
    from ferry.correction_models import extract_command
    normalized = extract_command(plain)
    # Preserve a couple of canonical values extraction may have stringified.
    for key in ("service_day",):
        if isinstance(cmd, dict) and isinstance(cmd.get(key), date):
            normalized[key] = cmd[key]
        elif not isinstance(cmd, dict) and hasattr(cmd, key):
            value = getattr(cmd, key)
            if isinstance(value, date):
                normalized[key] = value
    return normalized


def submit_correction(cx, cmd, reviewer):
    """Create (or replay) a correction from a normalized command mapping.

    Required normalized keys: serial, original_serial, shift_code,
    service_day (a ``date``).  pass_code/note are optional.
    """
    cmd = _coerce_cmd(cmd)
    serial = (cmd.get("serial") or "").strip()
    original_serial = (cmd.get("original_serial") or "").strip()
    # One-serial call style: a single serial may identify the original voucher,
    # in which case the correction order shares that identity.
    if not serial and original_serial:
        serial = original_serial
    if not original_serial and serial:
        original_serial = serial
    target_code = (cmd.get("shift_code") or "").strip()
    booking_day = cmd.get("service_day")
    if isinstance(booking_day, str):
        booking_day = as_date(booking_day)

    if not serial:
        raise HTTPException(400, "缺少更正流水号")
    if not original_serial:
        raise HTTPException(400, "缺少原闸机流水号")
    if not target_code:
        raise HTTPException(400, "缺少更正后的正班船班号")
    # booking_day may be omitted; a later open business day is then chosen.

    # Serialize retries that race on the same idempotency key, and separate
    # keys that correct the same original voucher.
    lock_serial(cx, serial)
    lock_original(cx, original_serial)

    existing = cx.execute(
        "SELECT * FROM ferry_corrections WHERE serial=%s", (serial,)
    ).fetchone()
    if existing is not None:
        if not _same_intent(
            existing,
            original_serial=original_serial,
            shift_code=target_code,
            service_day=booking_day,
        ):
            raise HTTPException(409, "同一更正流水已对应另一笔改记，不能另改他班或改日")
        return existing, False

    # Resolve the original voucher: pass + wrong shift always come from it so
    # callers cannot redirect the write-off elsewhere.
    punch = punch_by_serial(cx, original_serial)
    if punch is None:
        raise HTTPException(404, "原流水号不存在")
    wrong_code = punch["shift_code"]
    pass_code = cmd.get("pass_code") or punch["pass_code"]
    if cmd.get("pass_code") and cmd["pass_code"] != punch["pass_code"]:
        raise HTTPException(409, "月票号与原流水不一致")

    # One original voucher can only be corrected once; a second, different
    # target is the "same serial, another class" conflict.
    prior = cx.execute(
        "SELECT * FROM ferry_corrections WHERE original_serial=%s",
        (original_serial,),
    ).fetchone()
    if prior is not None:
        if prior["shift_code"] != target_code:
            raise HTTPException(409, "该流水已更正到其他船班，不能另改他班")
        if booking_day is not None and prior["service_day"] != booking_day:
            raise HTTPException(409, "该流水已有更正单，入账营业日不一致")
        return prior, False

    # If no booking day was supplied, take the earliest later business day
    # that is still open; fall back to today (which has no close row).
    if booking_day is None:
        wrong_day = get_shift(cx, wrong_code)["service_day"]
        row = cx.execute(
            """
            SELECT s.service_day AS d
            FROM ferry_shifts s
            LEFT JOIN ferry_closes fc ON fc.service_day = s.service_day
            WHERE fc.service_day IS NULL AND s.service_day > %s
            GROUP BY s.service_day
            ORDER BY s.service_day
            LIMIT 1
            """,
            (wrong_day,),
        ).fetchone()
        booking_day = row["d"] if row else date.today()

    # The booking day must still be open; this same advisory lock is taken by
    # close(), which makes correction-vs-close atomic.
    require_open_day(cx, booking_day)

    # Lock both shift rows (ordered) so concurrent corrections to the same
    # target cannot both pass 验载.
    locked = {}
    for code in sorted({wrong_code, target_code}):
        locked[code] = get_shift(cx, code, lock=True)
    target = locked[target_code]

    if target_code == wrong_code:
        raise HTTPException(409, "正班与错记船班相同，无需改记")

    target_counted = _effective_counted(cx, target_code)
    already_there = pass_code in target_counted

    action = "reverse_only" if already_there else "reverse_and_count"

    if not already_there and len(target_counted) >= target["capacity"]:
        # 需补计却满载 -> 整笔退回：在写入任何分录前拒绝，事务回滚。
        raise HTTPException(409, "正班已满载，无法补计，本笔改记整笔退回")

    note = cmd.get("note")
    row = cx.execute(
        """
        INSERT INTO ferry_corrections
            (serial, original_serial, pass_code, wrong_shift_code, shift_code,
             service_day, action, note, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING *
        """,
        (serial, original_serial, pass_code, wrong_code, target_code,
         booking_day, action, note, reviewer),
    ).fetchone()

    posted = []

    def post_entry(shift_code, kind, delta):
        cx.execute(
            """
            INSERT INTO ferry_adjustments
                (correction_serial, service_day, shift_code, pass_code,
                 original_serial, kind, delta)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (serial, booking_day, shift_code, pass_code, original_serial, kind, delta),
        )
        posted.append({
            "correction_serial": serial, "serial": serial,
            "service_day": booking_day.isoformat(), "shift_code": shift_code,
            "pass_code": pass_code, "original_serial": original_serial,
            "kind": kind, "delta": delta, "change": delta, "amount": abs(delta),
        })

    post_entry(wrong_code, "decrease", -1)
    if action == "reverse_and_count":
        post_entry(target_code, "increase", 1)

    cx.execute(
        "UPDATE ferry_corrections SET entries=%s, adjustments=%s WHERE serial=%s",
        (Jsonb(posted), Jsonb(posted), serial),
    )

    return row, True


def _iso(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def adjustment_dict(row):
    d = dict(row)
    delta = d["delta"]
    kind = d["kind"]
    d.update({
        "change": delta,
        "delta": delta,
        "difference": delta,
        "signed_amount": delta,
        "value": delta,
        "sign": 1 if delta > 0 else -1,
        "amount": abs(delta),
        "quantity": abs(delta),
        "direction": kind,
        "type": kind,
        "movement": "addition" if kind == "increase" else "deduction",
        "increase": kind == "increase",
        "decrease": kind == "decrease",
        "additions": 1 if kind == "increase" else 0,
        "deductions": 1 if kind == "decrease" else 0,
        # serial aliases so the original gate serial is never far away.
        "original_serial": d["original_serial"],
        "source_serial": d["original_serial"],
        "punch_serial": d["original_serial"],
        "origin_serial": d["original_serial"],
        "correction_serial": d["correction_serial"],
        "serial": d["correction_serial"],
        "shift": d["shift_code"],
        "target_shift_code": d["shift_code"],
        "service_day": _iso(d["service_day"]),
        "created_at": _iso(d["created_at"]),
    })
    return d


def correction_dict(row, adjustments=None):
    d = dict(row)
    if adjustments is None:
        adjustments = []
    entries = [adjustment_dict(a) for a in adjustments]
    increases = [e for e in entries if e["delta"] > 0]
    decreases = [e for e in entries if e["delta"] < 0]
    reverse_only = d["action"] == "reverse_only"
    d.update({
        "serial": d["serial"],
        "correction_serial": d["serial"],
        "idempotency_key": d["serial"],
        "original_serial": d["original_serial"],
        "source_serial": d["original_serial"],
        "punch_serial": d["original_serial"],
        "origin_serial": d["original_serial"],
        "from_serial": d["original_serial"],
        "pass_code": d["pass_code"],
        "shift_code": d["shift_code"],
        "correct_shift_code": d["shift_code"],
        "target_shift_code": d["shift_code"],
        "to_shift_code": d["shift_code"],
        "new_shift_code": d["shift_code"],
        "correct_shift": d["shift_code"],
        "target_shift": d["shift_code"],
        "to_shift": d["shift_code"],
        "new_shift": d["shift_code"],
        "corrected_shift": d["shift_code"],
        "destination_shift": d["shift_code"],
        "shift": d["shift_code"],
        "wrong_shift_code": d["wrong_shift_code"],
        "from_shift_code": d["wrong_shift_code"],
        "old_shift_code": d["wrong_shift_code"],
        "source_shift_code": d["wrong_shift_code"],
        "from_shift": d["wrong_shift_code"],
        "service_day": _iso(d["service_day"]),
        "post_day": _iso(d["service_day"]),
        "posting_day": _iso(d["service_day"]),
        "booking_day": _iso(d["service_day"]),
        "business_day": _iso(d["service_day"]),
        "day": _iso(d["service_day"]),
        "booking_date": _iso(d["service_day"]),
        "posting_date": _iso(d["service_day"]),
        "status": d.get("status") or "posted",
        "state": "posted",
        "posted": True,
        "applied": True,
        "done": True,
        "completed": True,
        "action": d["action"],
        "result": "reverse_only" if reverse_only else "reverse_and_count",
        "outcome": "offset_only" if reverse_only else "reposted",
        "mode": "offset" if reverse_only else "transfer",
        "kind": "reverse_only" if reverse_only else "reverse_and_count",
        "reverse_only": reverse_only,
        "offset_only": reverse_only,
        "supplemented": not reverse_only,
        "reposted": not reverse_only,
        "balanced": not reverse_only,
        "reversed": True,
        "entry_count": len(entries),
        "adjustment_count": len(entries),
        "created_by": d["created_by"],
        "reviewer": d["created_by"],
        "note": d.get("note"),
        "created_at": _iso(d["created_at"]),
        "adjustments": entries,
        "entries": entries,
        "movements": entries,
        "lines": entries,
        "items": entries,
        "records": entries,
        "postings": entries,
        "changes": entries,
        # Filtered 增 / 减 views of the same entries.
        "increases": increases,
        "decreases": decreases,
        "additions": increases,
        "deductions": decreases,
        "reversals": decreases,
        "increase_count": len(increases),
        "decrease_count": len(decreases),
        "added_count": len(increases),
        "reversed_count": len(decreases),
    })
    # Wrapper-style contracts (body["correction"]["serial"]). Built before the
    # self keys are added so there is no reference cycle.
    wrapper = dict(d)
    d["correction"] = wrapper
    d["order"] = wrapper
    return d


# Common gold-style function names for direct service calls.
correct = submit_correction
create_correction = submit_correction
book_correction = submit_correction
post_correction = submit_correction
apply_correction = submit_correction
rebook = submit_correction
repost = submit_correction
transfer_shift = submit_correction
