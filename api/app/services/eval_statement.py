"""Generate the human-readable Evaluation Statement for a bid.

Mirrors the columnar structure used in the corpus's Evaluation Statements
template: criterion | required | submitted | meets | remarks.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import ActiveRules, AuditLog, Bid, EvalStatement, Validation


VERDICT_QUALIFIED = "qualified"
VERDICT_NOT_QUALIFIED = "not_qualified"
VERDICT_CONDITIONAL = "conditional"


def _summarize_evidence(check_id: str, ev: dict[str, Any]) -> tuple[str, str]:
    """Best-effort 'required' / 'submitted' columns for the eval statement table."""
    if check_id == "FR-VAL-1.5":
        bv = ev.get("bid_value_inr_cr")
        capacity = ev.get("computed_capacity_inr_cr")
        return f"≥ ₹{bv:.2f} Cr", f"₹{capacity:.2f} Cr"
    if check_id == "FR-VAL-1.6":
        return f"≥ ₹{ev.get('threshold_inr_cr', 0):.2f} Cr", f"₹{ev.get('best_turnover_inr_cr', 0):.2f} Cr"
    if check_id == "FR-VAL-1.7":
        return f"≥ ₹{ev.get('threshold_inr_cr', 0):.2f} Cr", f"₹{ev.get('best_project_value_inr_cr', 0):.2f} Cr"
    if check_id == "FR-VAL-1.8":
        t = ev.get("thresholds", {})
        return f"BW ≥ {t.get('breakwater')}Rmt; DR ≥ {t.get('dredging')}Cum", f"BW {ev.get('breakwater_rmt')}Rmt; DR {ev.get('dredging_cum')}Cum"
    if check_id == "FR-VAL-1.4":
        return f"≤ {ev.get('max_months')} months old", f"{ev.get('age_months')} months old"
    if check_id == "FR-VAL-1.9":
        return "Σ Bills = Grand Summary (±0.1%)", f"Σ ₹{ev.get('summed', 0):.2f} Cr vs Grand ₹{ev.get('grand_summary', 0):.2f} Cr ({ev.get('diff_pct')}% gap)"
    if check_id == "FR-VAL-1.2":
        bb = ev.get("bid_bond", {})
        return "Bid Bond present, valid 180+ days, ≥2% of bid value", f"₹{bb.get('amount_inr_cr', 0):.2f} Cr / {bb.get('validity_days', 0)} days"
    if check_id == "FR-VAL-1.3":
        return "BG payee = JV entity name", f"BG payee: {ev.get('payee', '?')}"
    return "Mandatory item", "Submitted"


def generate_eval_statement(db: Session, bid_id: int) -> EvalStatement:
    bid = db.get(Bid, bid_id)
    if not bid:
        raise ValueError(f"bid {bid_id} not found")

    findings = (
        db.query(Validation)
        .filter(Validation.bid_id == bid_id)
        .order_by(Validation.layer, Validation.check_id)
        .all()
    )
    fails = [f for f in findings if f.verdict == "fail"]
    warns = [f for f in findings if f.verdict == "warning"]

    if fails:
        verdict = VERDICT_NOT_QUALIFIED
    elif warns:
        verdict = VERDICT_CONDITIONAL
    else:
        verdict = VERDICT_QUALIFIED

    # Get latest active rules for context
    ar = (
        db.query(ActiveRules)
        .filter(ActiveRules.tender_id == bid.tender_id)
        .order_by(ActiveRules.version.desc())
        .first()
    )
    rules_version = ar.version if ar else 1

    # Build the columnar table mirroring the human evaluator format
    rows: list[dict[str, Any]] = []
    for f in findings:
        required, submitted = _summarize_evidence(f.check_id, f.evidence or {})
        rows.append({
            "check_id": f.check_id,
            "criterion": f.title,
            "required": required,
            "submitted": submitted,
            "meets": f.verdict == "pass",
            "verdict": f.verdict,
            "remarks": f.message,
            "citation": {
                "section": f.citation_section,
                "clause": f.citation_clause,
                "text": f.citation_text,
            },
        })

    reasons = [
        {"check_id": f.check_id, "title": f.title, "message": f.message}
        for f in fails
    ]

    summary = (
        f"Bid by {bid.vendor_name} is QUALIFIED — all 10 mandatory checks passed under ActiveRules v{rules_version}."
        if verdict == VERDICT_QUALIFIED
        else f"Bid by {bid.vendor_name} is NOT QUALIFIED — {len(fails)} of 10 mandatory checks failed (under ActiveRules v{rules_version})."
    )

    payload = {
        "tender_id": bid.tender_id,
        "bid_id": bid.id,
        "vendor_name": bid.vendor_name,
        "jv_partners": bid.jv_partners,
        "bid_value_inr_cr": bid.bid_value_inr,
        "active_rules_version": rules_version,
        "verdict": verdict,
        "summary": summary,
        "rows": rows,
        "reasons": reasons,
        "generated_at": datetime.utcnow().isoformat(),
    }

    # Upsert
    db.query(EvalStatement).filter(EvalStatement.bid_id == bid_id).delete()
    es = EvalStatement(
        bid_id=bid_id,
        verdict=verdict,
        reasons=reasons,
        summary=summary,
        json_payload=payload,
    )
    db.add(es)

    _write_audit(db, action="eval_generated", payload={
        "bid_id": bid_id, "vendor": bid.vendor_name,
        "verdict": verdict, "fail_count": len(fails),
    })
    db.commit()
    db.refresh(es)
    return es


def _write_audit(db: Session, action: str, payload: dict[str, Any]) -> None:
    last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last.this_hash if last else None
    # Use a single ts string used both to hash and to store, so verify() reproduces it.
    ts = datetime.utcnow().replace(microsecond=0)
    body = json.dumps(
        {"action": action, "payload": payload, "ts": ts.isoformat(), "actor": "system"},
        sort_keys=True,
    )
    digest = hashlib.sha256(((prev_hash or "") + body).encode()).hexdigest()
    db.add(AuditLog(action=action, payload=payload, prev_hash=prev_hash, this_hash=digest, ts=ts))
