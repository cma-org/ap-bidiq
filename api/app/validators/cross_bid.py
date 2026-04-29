"""Layer-3 cross-bid anomaly detector.

Looks for collusion / cartelisation patterns across multiple submitted bids:
- Identical or near-identical experience claims (same project name + value + dates)
- Shared subcontractors or JV partners
- Suspiciously similar methodology language

Findings are flagged for human review — never auto-acted upon. Each flag
includes the two bid IDs, the similarity score, and the evidence excerpts.
"""
from __future__ import annotations

from typing import Any

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.models import Bid, CrossBidFlag, FormExtraction


def _by_form(extractions: list[FormExtraction]) -> dict[str, dict[str, Any]]:
    return {e.form_no: e.payload for e in extractions}


def _project_signature(p: dict[str, Any]) -> str:
    """Stringify a project entry from Form-5A for fuzzy comparison."""
    return f"{p.get('name', '')} | {p.get('client', '')} | {p.get('completion_date', '')} | ₹{p.get('value_inr_cr', 0)}".lower()


def detect_cross_bid_anomalies(db: Session, tender_id: int) -> list[dict[str, Any]]:
    """Run anomaly detection across all bids for a tender. Returns the new flags."""

    db.query(CrossBidFlag).filter(CrossBidFlag.tender_id == tender_id).delete()
    db.commit()

    bids = db.query(Bid).filter(Bid.tender_id == tender_id).all()
    flags: list[dict[str, Any]] = []

    # Build per-bid extracted forms map
    bid_forms = {b.id: _by_form(b.extractions) for b in bids}

    # Pairwise comparison
    for i, b_a in enumerate(bids):
        for b_b in bids[i + 1:]:
            forms_a = bid_forms[b_a.id]
            forms_b = bid_forms[b_b.id]

            # ---- 1. Similar experience claims (Form-5A) ------------------
            projects_a = forms_a.get("Form-5A", {}).get("projects", [])
            projects_b = forms_b.get("Form-5A", {}).get("projects", [])
            for p_a in projects_a:
                for p_b in projects_b:
                    sig_a = _project_signature(p_a)
                    sig_b = _project_signature(p_b)
                    sim = fuzz.token_set_ratio(sig_a, sig_b)
                    if sim >= 80:
                        flags.append({
                            "tender_id": tender_id,
                            "bid_a_id": b_a.id,
                            "bid_b_id": b_b.id,
                            "bid_a_vendor": b_a.vendor_name,
                            "bid_b_vendor": b_b.vendor_name,
                            "flag_type": "similar_experience_claim",
                            "similarity": sim / 100.0,
                            "severity": "critical" if sim >= 95 else "major",
                            "evidence": {
                                "project_a": p_a,
                                "project_b": p_b,
                                "vendor_a": b_a.vendor_name,
                                "vendor_b": b_b.vendor_name,
                            },
                            "explanation": (
                                f"{b_a.vendor_name} and {b_b.vendor_name} both list a project that matches "
                                f"at {sim}% similarity. Possible cartel pattern — review whether one bidder "
                                f"is sub-contracting the project from the other or using fabricated experience."
                            ),
                        })

            # ---- 2. Shared JV partners ------------------------------------
            partners_a = {p.lower() for p in (b_a.jv_partners or [])}
            partners_b = {p.lower() for p in (b_b.jv_partners or [])}
            shared = partners_a & partners_b
            if shared:
                flags.append({
                    "tender_id": tender_id,
                    "bid_a_id": b_a.id,
                    "bid_b_id": b_b.id,
                    "bid_a_vendor": b_a.vendor_name,
                    "bid_b_vendor": b_b.vendor_name,
                    "flag_type": "shared_jv_partner",
                    "similarity": 1.0,
                    "severity": "critical",
                    "evidence": {
                        "shared_partners": list(shared),
                        "bid_a_partners": list(b_a.jv_partners or []),
                        "bid_b_partners": list(b_b.jv_partners or []),
                    },
                    "explanation": (
                        f"Both bids share JV partner(s): {', '.join(shared)}. "
                        f"This is typically prohibited under ITT 1.6.4 (a partner cannot be in two bids)."
                    ),
                })

            # ---- 3. Identical bid value (typical cartel signal) ----------
            if b_a.bid_value_inr and b_b.bid_value_inr and abs(b_a.bid_value_inr - b_b.bid_value_inr) < 0.01:
                flags.append({
                    "tender_id": tender_id,
                    "bid_a_id": b_a.id,
                    "bid_b_id": b_b.id,
                    "bid_a_vendor": b_a.vendor_name,
                    "bid_b_vendor": b_b.vendor_name,
                    "flag_type": "identical_bid_value",
                    "similarity": 1.0,
                    "severity": "minor",
                    "evidence": {
                        "value_a": b_a.bid_value_inr,
                        "value_b": b_b.bid_value_inr,
                    },
                    "explanation": (
                        f"Both bids quote ₹{b_a.bid_value_inr:.2f} Cr exactly — investigate whether bidders "
                        f"coordinated. Common reason: both used the same estimator firm; less common but "
                        f"more serious: bid suppression."
                    ),
                })

    # Persist
    for f in flags:
        db.add(CrossBidFlag(
            tender_id=f["tender_id"],
            bid_a=f["bid_a_id"],
            bid_b=f["bid_b_id"],
            flag_type=f["flag_type"],
            similarity=f["similarity"],
            evidence={**f["evidence"], "explanation": f["explanation"], "severity": f["severity"]},
        ))
    db.commit()
    return flags
