from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bid, FormExtraction
from app.services.eval_statement import generate_eval_statement
from app.validators.deterministic import persist_findings, run_deterministic_validators
from app.validators.llm_clause import persist_llm_findings, run_llm_validators

router = APIRouter(prefix="/bids", tags=["bids"])


@router.get("")
def list_bids(tender_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Bid)
    if tender_id is not None:
        q = q.filter(Bid.tender_id == tender_id)
    rows = q.order_by(Bid.submitted_at.desc()).all()
    return [
        {
            "id": b.id,
            "tender_id": b.tender_id,
            "vendor_name": b.vendor_name,
            "jv_partners": b.jv_partners,
            "bid_value_inr": b.bid_value_inr,
            "submitted_at": b.submitted_at.isoformat(),
            "extraction_count": len(b.extractions),
        }
        for b in rows
    ]


@router.post("/{bid_id}/validate")
def validate_bid(bid_id: int, db: Session = Depends(get_db)):
    """Run the full validation pipeline (L1 deterministic for v1) + generate eval statement."""
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    findings = run_deterministic_validators(db, bid_id)
    persist_findings(db, bid_id, findings)
    llm_findings, llm_model = run_llm_validators(db, bid_id)
    persist_llm_findings(db, bid_id, llm_findings, llm_model)
    es = generate_eval_statement(db, bid_id)
    return {
        "bid_id": bid_id,
        "verdict": es.verdict,
        "summary": es.summary,
        "finding_count": len(findings) + len(llm_findings),
        "fail_count": sum(1 for f in findings + llm_findings if f.verdict == "fail"),
        "model_versions": ["deterministic-v1", llm_model],
    }


@router.post("/validate-all")
def validate_all_for_tender(tender_id: int, db: Session = Depends(get_db)):
    bids = db.query(Bid).filter(Bid.tender_id == tender_id).all()
    out = []
    for b in bids:
        findings = run_deterministic_validators(db, b.id)
        persist_findings(db, b.id, findings)
        llm_findings, llm_model = run_llm_validators(db, b.id)
        persist_llm_findings(db, b.id, llm_findings, llm_model)
        es = generate_eval_statement(db, b.id)
        all_fails = sum(1 for f in findings + llm_findings if f.verdict == "fail")
        out.append({"bid_id": b.id, "vendor": b.vendor_name, "verdict": es.verdict, "fail_count": all_fails})
    return {"tender_id": tender_id, "results": out}


@router.get("/{bid_id}")
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    b = db.get(Bid, bid_id)
    if not b:
        raise HTTPException(404, "Bid not found")
    return {
        "id": b.id,
        "tender_id": b.tender_id,
        "vendor_name": b.vendor_name,
        "jv_partners": b.jv_partners,
        "bid_value_inr": b.bid_value_inr,
        "submitted_at": b.submitted_at.isoformat(),
        "notes": b.notes,
        "extractions": [
            {"form_no": e.form_no, "confidence": e.confidence, "payload": e.payload}
            for e in b.extractions
        ],
    }
