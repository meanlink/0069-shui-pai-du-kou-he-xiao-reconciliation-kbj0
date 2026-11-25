from fastapi import APIRouter, Depends
from core import db, require
from ferry.dispute_logic import adjudicate, open_ticket
from ferry.dispute_models import Appeal, Decision
from ferry.dispute_store import get_disputes

router = APIRouter(prefix="/api/ferry")

@router.get("/disputes")
def disputes(_=Depends(require())):
    with db() as cx:
        return get_disputes(cx)

@router.post("/disputes", status_code=201)
def create_dispute(data: Appeal, _=Depends(require("operator"))):
    with db() as cx:
        return open_ticket(cx, data)

@router.put("/disputes/{serial}")
def finish_dispute(serial: str, data: Decision, _=Depends(require("reviewer"))):
    with db() as cx:
        return adjudicate(cx, serial, data)
