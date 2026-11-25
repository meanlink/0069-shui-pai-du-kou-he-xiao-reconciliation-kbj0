from fastapi import APIRouter, Depends
from core import db, require
from ferry.passbook import available_passes
from ferry.punch_logic import register
from ferry.punch_models import Punch
from ferry.punch_store import list_punches

router = APIRouter(prefix="/api/ferry")

@router.get("/passes")
def passes(_=Depends(require())):
    with db() as cx:
        return available_passes(cx)

@router.get("/punches")
def punches(_=Depends(require())):
    with db() as cx:
        return list_punches(cx)

@router.post("/punches", status_code=201)
def add_punch(body: Punch, _=Depends(require("operator"))):
    with db() as cx:
        return register(cx, body)
