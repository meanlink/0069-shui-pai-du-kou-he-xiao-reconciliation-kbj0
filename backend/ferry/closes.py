from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from core import db, enqueue, require
from ferry.close_store import get_close
from ferry.exports import as_csv
from ferry.settlement import close, summary

router = APIRouter(prefix="/api/ferry")

@router.get("/daily/{day}")
def daily_view(day: date, _=Depends(require())):
    with db() as cx:
        return summary(cx, day)

@router.post("/daily/{day}/close", status_code=201)
def daily_close(day: date, user=Depends(require("reviewer"))):
    with db() as cx:
        receipt = close(cx, day, user["email"])
        receipt["job"] = enqueue(cx, "settlement", {"day": day.isoformat()})
        return receipt

@router.get("/daily/{day}/download")
def daily_download(day: date, _=Depends(require())):
    with db() as cx:
        receipt = get_close(cx, day)
    if not receipt:
        raise HTTPException(409, "营业日封账后才可下载")
    return Response(as_csv(receipt["rows"]), media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=ferry-{day}.csv"})
