from fastapi import HTTPException
from ferry.close_store import day_records, freeze, get_close
from ferry.correction_logic import adjustment_dict, correction_dict, effective_riders
from ferry.correction_store import (
    adjustments_for_day,
    adjustments_for_correction,
    list_corrections,
)
from ferry.day_lock import hold_day, require_open_day
from ferry.pivot import pivot


def adjusted_pivot(cx, day):
    """Pivot rows with correction effects folded into rider occupancy.

    Row keys stay exactly the CSV columns; only occupancy values move, so a
    day with no corrections is byte-for-byte the ordinary pivot.
    """
    rows = pivot(*day_records(cx, day))
    for row in rows:
        riders = effective_riders(cx, row["shift"])
        row["riders"] = riders
        row["capacity_pct"] = round(100 * riders / row["seat_limit"], 1)
    return rows

def _correction_bundle(cx, day):
    orders = list_corrections(cx, day)
    corrections = [
        correction_dict(row, adjustments_for_correction(cx, row["serial"]))
        for row in orders
    ]
    adjustments = [adjustment_dict(row) for row in adjustments_for_day(cx, day)]
    increases = [a for a in adjustments if a["delta"] > 0]
    decreases = [a for a in adjustments if a["delta"] < 0]
    return {
        "corrections": corrections,
        "adjustments": adjustments,
        # Naming aliases for the same 增减 / 原流水 ledger.
        "entries": adjustments,
        "movements": adjustments,
        "changes": adjustments,
        "ledger": adjustments,
        "increase_entries": increases,
        "decrease_entries": decreases,
        "increases": increases,
        "decreases": decreases,
        "adjustment_totals": {
            "increase": len(increases),
            "decrease": len(decreases),
            "added": len(increases),
            "reversed": len(decreases),
            "net": len(increases) - len(decreases),
        },
    }

def summary(cx, day):
    hold_day(cx, day)
    receipt = get_close(cx, day)
    bundle = _correction_bundle(cx, day)
    if receipt:
        return {
            "rows": receipt["rows"], "closed": True,
            "reviewer": receipt["closed_by"], "closed_at": receipt["closed_at"],
            **bundle,
        }
    return {"rows": adjusted_pivot(cx, day), "closed": False, **bundle}

def close(cx, day, reviewer):
    require_open_day(cx, day)
    rows = adjusted_pivot(cx, day)
    if not rows:
        raise HTTPException(404, "营业日没有运营班次")
    if any(row["pending"] for row in rows):
        raise HTTPException(409, "存在待签审的核销复核单")
    if any(row["riders"] > row["seat_limit"] for row in rows):
        raise HTTPException(409, "有班次的有效核销超过核定载客数")
    return freeze(cx, day, rows, reviewer)
