import hashlib
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit(limit: int = 200, db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "ts": r.ts.isoformat(),
            "actor": r.actor,
            "action": r.action,
            "payload": r.payload,
            "prev_hash": r.prev_hash,
            "this_hash": r.this_hash,
            "note": r.note,
        }
        for r in reversed(rows)
    ]


@router.get("/verify")
def verify_chain(db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    bad: list[int] = []
    prev = None
    for r in rows:
        # Strip microseconds — writer normalised to whole-second precision.
        ts = r.ts.replace(microsecond=0)
        body = json.dumps(
            {"action": r.action, "payload": r.payload, "ts": ts.isoformat(), "actor": r.actor},
            sort_keys=True,
        )
        digest = hashlib.sha256(((prev or "") + body).encode()).hexdigest()
        if digest != r.this_hash or prev != r.prev_hash:
            bad.append(r.id)
        prev = r.this_hash
    return {"checked": len(rows), "broken_rows": bad, "ok": len(bad) == 0}
