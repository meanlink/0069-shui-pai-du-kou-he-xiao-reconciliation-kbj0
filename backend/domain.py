from fastapi import APIRouter
from ferry import closes, corrections, disputes, punches, shifts
from ferry.demo import seed
from ferry.receipt_worker import certify

router = APIRouter()
for segment in (shifts, punches, disputes, closes, corrections):
    router.include_router(segment.router)
router.include_router(corrections.root_router)

def run_job(cx, kind, payload):
    if kind == "settlement":
        return certify(cx,payload)
    raise ValueError(f"Unknown ferry task {kind}")
