"""AI Drafting Assistant.

Given a project brief (name, department, type, budget, location, etc.), the
assistant uses RAG over our existing tender's clause library + section
boilerplate to generate a draft RFP Section 1 (ITT) for the new project.

Backed by OpenAI GPT-4o (configurable per-deployment). Falls back to a
deterministic template when no key is set or the LLM call fails — so the
demo runs even offline.
"""
from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import MandatoryClause, Section, Tender
from app.services.llm import LLMUnavailable, chat_json, get_strong_model_label


SYSTEM_PROMPT = """You are an AP procurement officer drafting an RFP Section 1 (Instructions to Tenderers).

Output a JSON object with this exact shape (no markdown, no commentary):
{
  "title": "...",
  "subsections": [
    {"heading": "1.1 ...", "body": "concise clause text 2-4 sentences", "cited_clauses": ["MAND-..."]}
  ],
  "thresholds_table": [
    {"label": "...", "value": "...", "source": "..."}
  ],
  "ai_notes": "officer attention items"
}

Rules:
- 5-6 subsections covering: scope, eligibility, EMD, qualification, JV, integrity.
- Each body 2-4 sentences max.
- Cite mandatory clause codes from the provided library by code.
- Compute numeric thresholds from the brief budget (EMD = 2%; min turnover ≈ 92% of budget; min similar-work ≈ 46% of budget).
"""


def _stub_draft(brief: dict[str, Any], clauses: list[MandatoryClause]) -> dict[str, Any]:
    budget = float(brief.get("budget_inr_cr", 100.0))
    return {
        "title": f"Section 1 — Instructions to Tenderers — {brief.get('project_name', 'New Project')}",
        "subsections": [
            {
                "heading": "1.1 Scope of Tender",
                "body": f"The {brief.get('department', 'Department')} invites sealed bids for {brief.get('project_name', 'the project')} located at {brief.get('location', '[location]')} on EPCC turnkey basis. Estimated value: ₹{budget:.2f} Cr.",
                "cited_clauses": ["MAND-COMPANY-REG"],
            },
            {
                "heading": "1.2 Eligibility (Form-3)",
                "body": "Bidders shall furnish proof of valid company registration, PAN, GST, EPF and ESI certificates in the bidder entity name. JV bids are permitted with up to 3 partners.",
                "cited_clauses": ["MAND-COMPANY-REG", "MAND-PAN-GST", "MAND-EPF-ESI"],
            },
            {
                "heading": "1.3 Earnest Money Deposit (Form-B)",
                "body": f"EMD of ₹{budget * 0.02:.2f} Cr (2% of estimated cost) shall be furnished as a Bank Guarantee from a scheduled commercial bank, valid for 180 days from bid submission.",
                "cited_clauses": ["MAND-EMD"],
            },
            {
                "heading": "1.4 Qualification Requirements (Form-4, 5A, 5C)",
                "body": f"Annual turnover ≥ ₹{budget * 0.92:.2f} Cr in any one of last 7 years. Similar work value ≥ ₹{budget * 0.46:.2f} Cr in any one of last 5 years. Audited financial statements (3 yrs).",
                "cited_clauses": ["MAND-FIN-3YR", "MAND-EXP-CERT"],
            },
            {
                "heading": "1.5 Available Bid Capacity (Form-6A)",
                "body": "Available Bid Capacity = A × N × 3 − B, where A is the maximum annual contract value executed in any year of the last 10 years (per Corrigendum-1 reference). Capacity must be ≥ submitted Bid Value.",
                "cited_clauses": ["MAND-FIN-3YR"],
            },
            {
                "heading": "1.6 JV Agreement (Form-14) + Integrity Pact (Form-13)",
                "body": "If consortium: signed JV agreement establishing joint and several liability through defects-liability period. Integrity Pact must be signed by the same authorised signatory listed in Form-2 PoA.",
                "cited_clauses": ["MAND-JV-AGREEMENT", "MAND-LEAD-POA", "MAND-INTEGRITY-PACT"],
            },
        ],
        "thresholds_table": [
            {"label": "Estimated cost", "value": f"₹{budget:.2f} Cr", "source": "Project brief"},
            {"label": "EMD (2%)", "value": f"₹{budget * 0.02:.2f} Cr", "source": "Standard 2% of estimated cost"},
            {"label": "Min annual turnover", "value": f"₹{budget * 0.92:.2f} Cr", "source": "QR 3.1 — typical 92% of project value"},
            {"label": "Min similar-work value", "value": f"₹{budget * 0.46:.2f} Cr", "source": "QR 4.1 — typical 46% of project value"},
            {"label": "EMD validity", "value": "180 days", "source": "ITT 1.12"},
            {"label": "Bid capacity lookback", "value": "10 years", "source": "Corrigendum-1 amendment to ITT 1.6.1"},
        ],
        "ai_notes": (
            "STUB MODE — running without LLM. Officer should review: (a) whether 2% EMD is appropriate "
            "for the contract type, (b) whether the lookback period reflects current corrigenda, (c) special "
            "requirements specific to this project type that may need additional clauses."
        ),
    }


def draft_section_1(db: Session, tender_id: int, brief: dict[str, Any]) -> dict[str, Any]:
    tender = db.get(Tender, tender_id)
    if not tender:
        raise ValueError(f"Reference tender {tender_id} not found")

    clauses = (
        db.query(MandatoryClause)
        .filter(MandatoryClause.tender_id == tender_id)
        .all()
    )
    section_1 = (
        db.query(Section)
        .filter(Section.tender_id == tender_id, Section.name.like("%Section 1%"))
        .first()
    )

    # Tight RAG context: clause CODES + titles only (no full text), plus a short reference.
    clause_library = [{"code": c.code, "title": c.title} for c in clauses]
    reference_excerpt = (section_1.raw_text[:2500] if section_1 else "(no reference)")

    user_prompt = f"""PROJECT BRIEF:
{json.dumps(brief, indent=2)}

MANDATORY CLAUSES (cite by code):
{json.dumps(clause_library, indent=2)}

REFERENCE Section 1 EXCERPT (for tone):
\"\"\"
{reference_excerpt}
\"\"\"

Generate the JSON now.
"""

    try:
        result = chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=2500,
            temperature=0.2,
        )
        result["model_version"] = f"drafting-{get_strong_model_label()}"
        return result
    except LLMUnavailable:
        result = _stub_draft(brief, clauses)
        result["model_version"] = "drafting-stub-no-key"
        return result
    except (ValueError, Exception) as e:  # noqa: BLE001
        result = _stub_draft(brief, clauses)
        result["model_version"] = f"drafting-stub-after-error: {type(e).__name__}"
        result["ai_notes"] = (
            f"LLM call failed ({type(e).__name__}): falling back to deterministic template. "
            "In production, the system would retry with stricter prompting or split into per-section calls. "
        ) + result.get("ai_notes", "")
        return result
