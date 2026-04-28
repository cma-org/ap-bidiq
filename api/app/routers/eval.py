from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import EvalStatement, Bid
from app.services.eval_docx import render_eval_statement_docx

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


@router.get("/by-bid/{bid_id}/docx")
def download_eval_docx(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    try:
        data = render_eval_statement_docx(db, bid_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    safe_vendor = "".join(c if c.isalnum() else "_" for c in bid.vendor_name)[:60]
    filename = f"Evaluation_Statement_{safe_vendor}.docx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
