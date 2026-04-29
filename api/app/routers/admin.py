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
    x_admin_token: str | None = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
):
    """Drop existing tender + bids, re-ingest corpus + load all synthetic bids."""
    _check(x_admin_token)

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
        "tender_id": report.tender_id,
        "sections_loaded": report.sections_loaded,
        "corrigenda_loaded": report.corrigenda_loaded,
        "patches_detected": report.patches_detected,
        "active_rule_versions": report.active_rule_versions,
        "synthetic_bids_loaded": bid_count,
    }
