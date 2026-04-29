from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.drafting import draft_section_1

router = APIRouter(prefix="/draft", tags=["drafting"])


@router.post("/section-1")
def post_draft_section_1(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Generate a draft Section 1 (ITT) for a new project.

    Body example:
    {
      "tender_id": 1,        # reference tender to use as clause library
      "brief": {
        "project_name": "Krishnapatnam Outer Harbour Phase III",
        "department": "Infrastructure & Investment Department, AP",
        "project_type": "Marine works (EPCC)",
        "budget_inr_cr": 425.0,
        "location": "Krishnapatnam, AP",
        "duration_years": 3,
        "special_requirements": "Includes 1.5 km breakwater, dredging 600,000 cum, deep-water piling"
      }
    }
    """
    tender_id = int(payload.get("tender_id", 1))
    brief = payload.get("brief") or {}
    if not brief:
        raise HTTPException(400, "brief is required")
    try:
        result = draft_section_1(db, tender_id, brief)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result
