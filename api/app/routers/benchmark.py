from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bid, Validation, EvalStatement

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


@router.get("")
def benchmark_summary(tender_id: int | None = None, db: Session = Depends(get_db)):
    """Live benchmark report: per-bid verdicts vs. ground truth labels."""
    q = db.query(Bid)
    if tender_id is not None:
        q = q.filter(Bid.tender_id == tender_id)
    bids = q.all()

    rows = []
    total_expected_findings = 0
    total_caught_findings = 0
    correct_verdicts = 0

    for b in bids:
        truth = (b.notes or "{}")
        # ground-truth labels are stored as JSON in bid.notes for the demo seed.
        import json
        try:
            label = json.loads(truth)
        except json.JSONDecodeError:
            label = {}

        expected_findings: list[str] = label.get("expected_findings", [])
        expected_verdict: str | None = label.get("verdict")

        validations = db.query(Validation).filter(Validation.bid_id == b.id).all()
        actual_failures = {v.check_id for v in validations if v.verdict == "fail"}

        es = (
            db.query(EvalStatement)
            .filter(EvalStatement.bid_id == b.id)
            .order_by(EvalStatement.generated_at.desc())
            .first()
        )
        actual_verdict = es.verdict if es else None

        caught = sorted(set(expected_findings) & actual_failures)
        missed = sorted(set(expected_findings) - actual_failures)
        false_positives = sorted(actual_failures - set(expected_findings))

        verdict_match = (
            (expected_verdict == "Qualified" and actual_verdict == "qualified") or
            (expected_verdict == "Not Qualified" and actual_verdict == "not_qualified")
        )

        if verdict_match:
            correct_verdicts += 1
        total_expected_findings += len(expected_findings)
        total_caught_findings += len(caught)

        rows.append({
            "bid_id": b.id,
            "vendor_name": b.vendor_name,
            "expected_verdict": expected_verdict,
            "actual_verdict": actual_verdict,
            "verdict_match": verdict_match,
            "expected_findings": expected_findings,
            "caught_findings": caught,
            "missed_findings": missed,
            "false_positives": false_positives,
        })

    detection_rate = (
        (total_caught_findings / total_expected_findings) if total_expected_findings else 0.0
    )
    verdict_rate = (correct_verdicts / len(bids)) if bids else 0.0

    return {
        "bid_count": len(bids),
        "defect_detection_rate": round(detection_rate, 3),
        "verdict_match_rate": round(verdict_rate, 3),
        "false_positive_count": sum(len(r["false_positives"]) for r in rows),
        "rows": rows,
    }
