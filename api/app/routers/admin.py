"""Admin endpoints for the demo. In production these would require auth + RBAC."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.ingest.rfp import ingest_corpus
from app.ingest.synthetic_bids import seed_synthetic_bids

router = APIRouter(prefix="/admin", tags=["admin"])


def _check(token: str | None) -> None:
    expected = os.environ.get("ADMIN_TOKEN")
    if not expected:
        return  # demo mode — no token gate
    if token != expected:
        raise HTTPException(401, "X-Admin-Token mismatch")


@router.post("/reseed")
def reseed(
    hard_reset: bool = False,
    x_admin_token: str | None = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
):
    """Re-ingest corpus + load all synthetic bids.

    Set hard_reset=true to drop ALL tenders + bids first (clean slate).
    """
    _check(x_admin_token)

    if hard_reset:
        from sqlalchemy import text
        from app.models import (
            ActiveRules, AuditLog, Bid, Corrigendum, CrossBidFlag, EvalStatement,
            FormExtraction, FormRequired, MandatoryClause, Patch, Section, Tender,
            Validation,
        )
        # Order matters for FK constraints
        for model in [Validation, EvalStatement, CrossBidFlag, FormExtraction, Bid,
                      Patch, Corrigendum, ActiveRules, Section, FormRequired,
                      MandatoryClause, AuditLog, Tender]:
            db.query(model).delete()
        db.commit()
        # Reset Postgres sequences so re-ingest produces id=1 again (keeps the
        # hardcoded /tenders/1 URLs in the UI valid). Skip on SQLite.
        if "postgres" in str(db.bind.url):
            for seq in ["tenders_id_seq", "bids_id_seq", "sections_id_seq",
                        "corrigenda_id_seq", "patches_id_seq", "active_rules_id_seq",
                        "forms_required_id_seq", "mandatory_clauses_id_seq",
                        "form_extractions_id_seq", "validations_id_seq",
                        "cross_bid_flags_id_seq", "eval_statements_id_seq",
                        "audit_log_id_seq"]:
                try:
                    db.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
                except Exception:
                    pass
            db.commit()

    settings = get_settings()
    candidates = [
        Path(settings.corpus_dir),
        Path(__file__).resolve().parent.parent.parent / "data" / "corpus",
        Path("/app/data/corpus"),
    ]
    corpus_dir = next((p for p in candidates if p.exists()), None)
    if not corpus_dir:
        raise HTTPException(500, "Corpus directory not found in any expected location")

    report = ingest_corpus(db, corpus_dir)
    bid_count = seed_synthetic_bids(db, report.tender_id)

    return {
        "ok": True,
        "hard_reset": hard_reset,
        "tender_id": report.tender_id,
        "sections_loaded": report.sections_loaded,
        "corrigenda_loaded": report.corrigenda_loaded,
        "patches_detected": report.patches_detected,
        "active_rule_versions": report.active_rule_versions,
        "synthetic_bids_loaded": bid_count,
    }
