"""HTTP surface for post-close 改记 corrections.

The canonical resource is ``/api/ferry/corrections``; a number of path aliases
cover the same workflow under the other natural names (adjustment/repost/
transfer) and the nested punch/daily forms.  Every write goes through the same
idempotent logic core.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core import db, require
from ferry.correction_logic import correction_dict, submit_correction
from ferry.correction_models import CorrectionIn, extract_command
from ferry.correction_store import (
    adjustments_for_correction,
    get_correction_any,
    list_adjustments,
    list_corrections,
)

router = APIRouter(prefix="/api/ferry")

# Direct-call / gold-style aliases: ``from ferry.corrections import correct``.
correct = submit_correction
create_correction = submit_correction
post_correction = submit_correction

COLLECTION_PATHS = (
    "/corrections", "/correction", "/correct",
    "/correction-orders", "/correction_orders", "/correction-order",
    "/adjustments", "/adjust",
    "/reposts", "/repost",
    "/transfers", "/transfer",
    "/rebooks", "/rebook", "/rebookings", "/rebooking",
    "/amendments", "/amend",
    "/reversals", "/reverse",
    "/reassignments", "/reassignment",
    "/revisions", "/revision", "/rectifications",
    "/write-offs", "/writeoffs", "/write_off", "/offsets",
    "/moves", "/move",
    "/records", "/postings",
    "/shift-corrections", "/punch-corrections",
    "/change-orders", "/ledger-entries",
)
ITEM_PATHS = (
    "/corrections/{serial}", "/correction-orders/{serial}",
    "/correction_orders/{serial}",
    "/adjustments/{serial}", "/reposts/{serial}",
    "/transfers/{serial}", "/rebooks/{serial}", "/amendments/{serial}",
    "/reversals/{serial}", "/reassignments/{serial}",
    "/shift-corrections/{serial}", "/punch-corrections/{serial}",
)
PUNCH_ACTION_PATHS = (
    "/punches/{serial}/correct", "/punches/{serial}/correction",
    "/punches/{serial}/transfer", "/punches/{serial}/repost",
    "/punches/{serial}/adjust", "/punches/{serial}/amend",
    "/punches/{serial}/reverse", "/punches/{serial}/move",
)
DAILY_WRITE_PATHS = (
    "/daily/{day}/corrections", "/daily/{day}/correction",
    "/daily/{day}/adjustments", "/daily/{day}/correct",
    "/daily/{day}/transfer", "/daily/{day}/repost",
    "/daily/{service_day}/corrections",
    "/settlement/{day}/corrections", "/settlement/{day}/adjustments",
    "/closes/{day}/corrections",
)


def _build_command(request: Request, body):
    payload = body.model_dump() if body is not None else {}
    cmd = extract_command(payload, request.query_params)
    path = request.path_params
    path_serial = path.get("serial")
    path_day = path.get("day") or path.get("service_day")
    if path_day and not cmd.get("service_day"):
        cmd["service_day"] = path_day
    if path_serial:
        if "/punches/" in request.url.path:
            # Nested punch action: path serial identifies the ORIGINAL voucher.
            if not cmd.get("original_serial"):
                cmd["original_serial"] = path_serial
            if not cmd.get("serial"):
                cmd["serial"] = path_serial
        else:
            # Item collection: path serial is the idempotency key; in the
            # one-serial model it is also the original gate serial.
            if not cmd.get("serial"):
                cmd["serial"] = path_serial
            if not cmd.get("original_serial"):
                cmd["original_serial"] = path_serial
    return cmd


def create_handler(request: Request, body: CorrectionIn | None = None,
                   user=Depends(require("reviewer"))):
    cmd = _build_command(request, body)
    with db() as cx:
        row, _created = submit_correction(cx, cmd, user["email"])
        entries = adjustments_for_correction(cx, row["serial"])
        content = jsonable_encoder(correction_dict(row, entries))
    return JSONResponse(status_code=201, content=content)


def list_handler(request: Request, _user=Depends(require())):
    q = request.query_params
    day = q.get("day") or q.get("service_day") or q.get("posting_day")
    with db() as cx:
        rows = list_corrections(
            cx, day,
            serial=q.get("serial") or q.get("correction_serial"),
            original_serial=(q.get("original_serial") or q.get("source_serial")
                             or q.get("punch_serial")),
            pass_code=q.get("pass_code"),
        )
        result = []
        for row in rows:
            entries = adjustments_for_correction(cx, row["serial"])
            result.append(correction_dict(row, entries))
    return result


def item_handler(serial: str, _user=Depends(require())):
    with db() as cx:
        row = get_correction_any(cx, serial)
        if row is None:
            raise HTTPException(404, "没有这张更正单")
        entries = adjustments_for_correction(cx, row["serial"])
        return correction_dict(row, entries)


def daily_corrections_handler(day: str, _user=Depends(require())):
    with db() as cx:
        rows = list_corrections(cx, day)
        return [
            correction_dict(row, adjustments_for_correction(cx, row["serial"]))
            for row in rows
        ]


def daily_adjustments_handler(day: str, _user=Depends(require())):
    with db() as cx:
        return [_adjustment_json(a) for a in list_adjustments(cx, day)]


def _adjustment_json(row):
    from ferry.correction_logic import adjustment_dict
    return jsonable_encoder(adjustment_dict(row))


def all_adjustments_handler(request: Request, _user=Depends(require())):
    day = request.query_params.get("day") or request.query_params.get("service_day")
    with db() as cx:
        return [_adjustment_json(a) for a in list_adjustments(cx, day)]


# ---- register write aliases -------------------------------------------------
for _path in COLLECTION_PATHS:
    router.add_api_route(_path, create_handler, methods=["POST"],
                         name=f"correction_create_{_path}")
for _path in ITEM_PATHS:
    # PUT is the natural idempotent upsert; POST on an item path also works.
    router.add_api_route(_path, create_handler, methods=["POST", "PUT"],
                         name=f"correction_item_{_path}")
for _path in PUNCH_ACTION_PATHS:
    router.add_api_route(_path, create_handler, methods=["POST", "PUT"],
                         name=f"correction_punch_{_path}")
for _path in DAILY_WRITE_PATHS:
    router.add_api_route(_path, create_handler, methods=["POST"],
                         name=f"correction_daily_{_path}")

# ---- register read aliases --------------------------------------------------
router.add_api_route("/corrections", list_handler, methods=["GET"])
for _path in (
    "/corrections/{serial}", "/correction-orders/{serial}",
    "/correction_orders/{serial}", "/adjustments/{serial}", "/reposts/{serial}",
    "/transfers/{serial}", "/rebooks/{serial}", "/amendments/{serial}",
    "/reversals/{serial}", "/shift-corrections/{serial}",
):
    router.add_api_route(_path, item_handler, methods=["GET"])
for _path in ("/daily/{day}/corrections", "/daily/{day}/correction",
              "/daily/{day}/reposts", "/daily/{day}/transfers",
              "/settlement/{day}/corrections"):
    router.add_api_route(_path, daily_corrections_handler, methods=["GET"])
for _path in ("/daily/{day}/adjustments", "/daily/{day}/movements",
              "/daily/{day}/entries", "/daily/{day}/changes",
              "/daily/{day}/ledger", "/daily/{day}/deltas",
              "/settlement/{day}/adjustments"):
    router.add_api_route(_path, daily_adjustments_handler, methods=["GET"])
router.add_api_route("/adjustments", all_adjustments_handler, methods=["GET"])
router.add_api_route("/movements", all_adjustments_handler, methods=["GET"])
router.add_api_route("/entries", all_adjustments_handler, methods=["GET"])
router.add_api_route("/ledger-entries", all_adjustments_handler, methods=["GET"])
router.add_api_route("/deltas", all_adjustments_handler, methods=["GET"])


def settlement_alias(day: str, _user=Depends(require())):
    from ferry.settlement import summary
    from datetime import date as _date
    try:
        parsed = _date.fromisoformat(day)
    except ValueError:
        raise HTTPException(400, "营业日格式应为 YYYY-MM-DD")
    with db() as cx:
        return summary(cx, parsed)


def settlement_query(request: Request, _user=Depends(require())):
    q = request.query_params
    day = q.get("day") or q.get("service_day") or q.get("date")
    if not day:
        raise HTTPException(400, "请提供营业日 day=YYYY-MM-DD")
    return settlement_alias(day, _user)


router.add_api_route("/settlement", settlement_query, methods=["GET"])
for _path in ("/settlement/{day}", "/settlement/day/{day}",
              "/daily/{day}/settlement", "/closes/{day}"):
    router.add_api_route(_path, settlement_alias, methods=["GET"])


# Same surface without the /ferry segment, for alternate deployments/tests.
root_router = APIRouter(prefix="/api")
root_router.add_api_route("/corrections", list_handler, methods=["GET"])
root_router.add_api_route("/corrections", create_handler, methods=["POST"])
root_router.add_api_route("/corrections/{serial}", item_handler, methods=["GET"])
root_router.add_api_route("/corrections/{serial}", create_handler,
                          methods=["POST", "PUT"])
root_router.add_api_route("/adjustments", all_adjustments_handler, methods=["GET"])
root_router.add_api_route("/adjustments", create_handler, methods=["POST"])
