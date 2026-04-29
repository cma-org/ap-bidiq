from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bid, CrossBidFlag
from app.validators.cross_bid import detect_cross_bid_anomalies

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.post("/detect")
def post_detect(tender_id: int, db: Session = Depends(get_db)):
    flags = detect_cross_bid_anomalies(db, tender_id)
    return {"tender_id": tender_id, "flag_count": len(flags), "flags": flags}


@router.get("/by-tender/{tender_id}")
def list_anomalies(tender_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(CrossBidFlag)
        .filter(CrossBidFlag.tender_id == tender_id)
        .order_by(CrossBidFlag.id.desc())
        .all()
    )
    out = []
    for r in rows:
        bid_a = db.get(Bid, r.bid_a)
        bid_b = db.get(Bid, r.bid_b)
        ev = r.evidence or {}
        out.append({
            "id": r.id,
            "bid_a_id": r.bid_a,
            "bid_b_id": r.bid_b,
            "bid_a_vendor": bid_a.vendor_name if bid_a else "?",
            "bid_b_vendor": bid_b.vendor_name if bid_b else "?",
            "flag_type": r.flag_type,
            "similarity": r.similarity,
            "severity": ev.get("severity", "info"),
            "explanation": ev.get("explanation", ""),
            "evidence": {k: v for k, v in ev.items() if k not in ("severity", "explanation")},
        })
    return out
