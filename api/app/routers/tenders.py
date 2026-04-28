from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Tender, Section, Corrigendum, ActiveRules, MandatoryClause, FormRequired

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.get("")
def list_tenders(db: Session = Depends(get_db)):
    rows = db.query(Tender).order_by(Tender.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "department": t.department,
            "code": t.code,
            "created_at": t.created_at.isoformat(),
            "section_count": len(t.sections),
            "corrigendum_count": len(t.corrigenda),
        }
        for t in rows
    ]


@router.get("/{tender_id}")
def get_tender(tender_id: int, db: Session = Depends(get_db)):
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "Tender not found")
    return {
        "id": t.id,
        "title": t.title,
        "department": t.department,
        "code": t.code,
        "created_at": t.created_at.isoformat(),
        "sections": [{"id": s.id, "name": s.name, "order_idx": s.order_idx, "char_count": len(s.raw_text)} for s in t.sections],
        "corrigenda": [{"id": c.id, "name": c.name, "order_idx": c.order_idx} for c in t.corrigenda],
        "mandatory_clauses_count": len(t.mandatory_clauses),
        "forms_required_count": len(t.forms_required),
    }


@router.get("/{tender_id}/active-rules")
def get_active_rules(tender_id: int, db: Session = Depends(get_db)):
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "Tender not found")
    latest = (
        db.query(ActiveRules)
        .filter(ActiveRules.tender_id == tender_id)
        .order_by(ActiveRules.version.desc())
        .first()
    )
    if not latest:
        raise HTTPException(404, "Active rules not yet generated for this tender")
    return {
        "tender_id": tender_id,
        "version": latest.version,
        "generated_at": latest.generated_at.isoformat(),
        "payload": latest.payload,
    }


@router.get("/{tender_id}/corrigendum-diff")
def get_corrigendum_diff(tender_id: int, db: Session = Depends(get_db)):
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "Tender not found")

    diffs = []
    for c in sorted(t.corrigenda, key=lambda x: x.order_idx):
        diffs.append({
            "corrigendum_id": c.id,
            "name": c.name,
            "patches": [
                {
                    "target_clause": p.target_clause,
                    "op": p.op,
                    "before": p.before_text,
                    "after": p.after_text,
                    "summary": p.semantic_summary,
                }
                for p in c.patches
            ],
        })
    return {"tender_id": tender_id, "corrigenda": diffs}


@router.get("/{tender_id}/mandatory-clauses")
def list_mandatory_clauses(tender_id: int, db: Session = Depends(get_db)):
    rows = db.query(MandatoryClause).filter(MandatoryClause.tender_id == tender_id).all()
    return [
        {
            "id": r.id,
            "code": r.code,
            "title": r.title,
            "source_section": r.source_section,
            "layer": r.layer,
            "source_text_preview": (r.source_text[:240] + "…") if len(r.source_text) > 240 else r.source_text,
        }
        for r in rows
    ]


@router.get("/{tender_id}/forms-required")
def list_forms_required(tender_id: int, db: Session = Depends(get_db)):
    rows = db.query(FormRequired).filter(FormRequired.tender_id == tender_id).all()
    return [{"id": r.id, "form_no": r.form_no, "title": r.title, "schema": r.schema} for r in rows]
