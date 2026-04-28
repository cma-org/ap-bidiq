from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Validation, Bid

router = APIRouter(prefix="/validations", tags=["validations"])


@router.get("/by-bid/{bid_id}")
def get_validations_for_bid(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    rows = (
        db.query(Validation)
        .filter(Validation.bid_id == bid_id)
        .order_by(Validation.layer, Validation.check_id)
        .all()
    )
    counts = {"pass": 0, "fail": 0, "warning": 0}
    for r in rows:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    return {
        "bid_id": bid_id,
        "summary": counts,
        "findings": [
            {
                "id": r.id,
                "check_id": r.check_id,
                "layer": r.layer,
                "verdict": r.verdict,
                "severity": r.severity,
                "title": r.title,
                "message": r.message,
                "citation": {
                    "section": r.citation_section,
                    "clause": r.citation_clause,
                    "text": r.citation_text,
                },
                "evidence": r.evidence,
            }
            for r in rows
        ],
    }
