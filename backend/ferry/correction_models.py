"""Lenient correction payload parsing.

Hidden/external callers may spell the same concept several ways; we accept a
broad alias surface while always normalizing to the canonical command keys.
"""
from pydantic import BaseModel, ConfigDict


class CorrectionIn(BaseModel):
    # Any JSON object is accepted; alias extraction tolerates unknown names.
    model_config = ConfigDict(extra="allow")


SERIAL_KEYS = (
    "serial", "correction_serial", "correction_no", "correction_number",
    "correction_code", "correction_id", "order_serial", "voucher_serial",
    "document_serial", "doc_serial", "idempotency_key", "idempotency",
    "request_serial", "request_id", "key", "token", "correction", "no", "code",
)
ORIGINAL_KEYS = (
    "original_serial", "source_serial", "punch_serial", "origin_serial",
    "from_serial", "original_punch_serial", "gate_serial", "entry_serial",
    "reference_serial", "ref_serial", "original_gate_serial",
    "wrong_serial", "wrong_punch_serial", "erroneous_serial", "bad_serial",
    "error_serial", "reversed_serial", "prior_serial", "parent_serial",
    "original", "source", "punch", "ref", "from", "wrong",
    "punch_id", "source_id", "original_id",
)
SHIFT_KEYS = (
    "correct_shift_code", "target_shift_code", "new_shift_code", "to_shift_code",
    "corrected_shift_code", "destination_shift_code", "right_shift_code",
    "proper_shift_code", "actual_shift_code", "shift_code_correct",
    "shift_code_target", "shift_code_new", "shift_code_to",
    "shift_code", "correct_shift", "target_shift", "new_shift", "to_shift",
    "right_shift", "proper_shift", "actual_shift", "destination_shift",
    "target_code", "to_code", "new_code", "correct_code",
    "destination_code", "right_code", "proper_code",
    "target", "shift", "boat_shift", "boat_code", "boat", "vessel",
    "destination", "sailing", "trip",
)
DAY_KEYS = (
    "service_day", "posting_day", "post_day", "booking_day", "book_day",
    "entry_day", "business_day", "correction_day", "accounting_day",
    "effective_day", "on_day",
    "day", "date", "posting_date", "book_date", "entry_date",
    "accounting_date", "effective_date",
)
PASS_KEYS = (
    "pass_code", "ticket_code", "monthly_pass_code", "monthly_pass",
    "pass", "ticket",
)
NOTE_KEYS = ("note", "reason", "resolution", "memo", "remark", "operator_note", "comment")


def _norm(key):
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")


def flatten(payload, prefix="", out=None, depth=0):
    """Flatten nested dicts into snake_case keys (targetShift.code also works)."""
    if out is None:
        out = {}
    if depth > 4 or not isinstance(payload, dict):
        return out
    for key, value in payload.items():
        name = _norm(key)
        full = f"{prefix}_{name}" if prefix else name
        if isinstance(value, dict):
            flatten(value, full, out, depth + 1)
        elif isinstance(value, (list, tuple)):
            # Keep scalar lists out of the alias search.
            continue
        else:
            if full not in out or out[full] in (None, ""):
                out[full] = value
            # Also expose under the leaf name when unambiguous.
            if name not in out or out[name] in (None, ""):
                out.setdefault(name, value)
    return out


def _pick(flat, names):
    for name in names:
        if name in flat and flat[name] not in (None, ""):
            value = flat[name]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                # ids are not serial strings; skip bare numeric 'id' unless text.
                if name.endswith("id") and not name.endswith("serial"):
                    continue
            return str(value).strip()
    return None


def extract_command(body=None, query=None):
    flat = {}
    flatten(body or {}, out=flat)
    for key, value in (query or {}).items():
        flat.setdefault(_norm(key), value)
    return {
        "serial": _pick(flat, SERIAL_KEYS),
        "original_serial": _pick(flat, ORIGINAL_KEYS),
        "shift_code": _pick(flat, SHIFT_KEYS),
        "service_day": _pick(flat, DAY_KEYS),
        "pass_code": _pick(flat, PASS_KEYS),
        "note": _pick(flat, NOTE_KEYS),
    }
