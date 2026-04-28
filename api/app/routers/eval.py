from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import EvalStatement, Bid

router = APIRouter(prefix="/eval", tags=["eval"])


@router.get("/by-bid/{bid_id}")
def get_eval(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    es = (
        db.query(EvalStatement)
        .filter(EvalStatement.bid_id == bid_id)
        .order_by(EvalStatement.generated_at.desc())
        .first()
    )
    if not es:
        raise HTTPException(404, "Evaluation statement not yet generated")
    return {
        "bid_id": bid_id,
        "verdict": es.verdict,
        "summary": es.summary,
        "reasons": es.reasons,
        "generated_at": es.generated_at.isoformat(),
        "json_payload": es.json_payload,
        "docx_path": es.docx_path,
    }
