from datetime import date
from hashlib import sha256
from ferry.close_store import get_close
from ferry.exports import as_csv

def certify(cx, payload):
    day = date.fromisoformat(payload["day"])
    receipt = get_close(cx, day)
    content = as_csv(receipt["rows"])
    return {"sha256": sha256(content.encode()).hexdigest(), "rows": len(receipt["rows"]), "day": day.isoformat()}
