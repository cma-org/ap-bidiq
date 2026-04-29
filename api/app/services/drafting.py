"""AI Drafting Assistant.

Given a project brief (name, department, type, budget, location, etc.), the
assistant uses RAG over our existing tender's clause library + section
boilerplate to generate a draft RFP Section 1 (ITT) for the new project.

This isn't a generic "write a tender" prompt — it's grounded in the AP/EPCC
clause set we already ingested, ensuring the draft uses the same legal
language and structure as the department's existing tenders.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import MandatoryClause, Section, Tender


SYSTEM_PROMPT = """You are an experienced procurement officer drafting an RFP Section 1 (Instructions to Tenderers) for the Government of Andhra Pradesh.

You will be given:
1. A project brief with key parameters (name, type, budget, location, etc.).
2. The mandatory clauses that must appear in any AP tender (the "clause library").
3. Excerpts from a reference tender Section 1 to use as structural inspiration.

Your job: produce a draft Section 1 (ITT) for the new project. Use formal AP procurement language. Cite the specific mandatory clauses by code in [brackets] when you reference them. Do not invent legal text — adapt the reference material.

Output a structured JSON object with this shape:
{
  "title": "string — section title",
  "subsections": [
    {"heading": "string", "body": "string — the actual clause text", "cited_clauses": ["MAND-XXX", ...]}
  ],
  "thresholds_table": [
    {"label": "string", "value": "string", "source": "string — where this is set"}
  ],
  "ai_notes": "string — any officer-attention items (gaps, decisions needed, items requiring SME review)"
}

Rules:
- Generate 6–8 subsections covering: scope, eligibility, EMD, qualification, JV, evaluation method, submission, validity.
- Cite at least 8 distinct mandatory clause codes across the document.
- Compute thresholds from the project brief (e.g., EMD = 2% of budget, similar work = 50% of budget).
- Flag any officer decision required in ai_notes.
- Output ONLY the JSON. No markdown fences, no commentary.
"""


def _client():
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None, None
    try:
        from anthropic import Anthropic  # type: ignore
        return Anthropic(api_key=settings.anthropic_api_key), settings.anthropic_model_strong
    except Exception:
        return None, None


def _stub_draft(brief: dict[str, Any], clauses: list[MandatoryClause]) -> dict[str, Any]:
    """Deterministic fallback when no API key — still demonstrates the structure."""
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
                "heading": "1.6 JV Agreement (Form-14)",
                "body": "If consortium: signed JV agreement establishing joint and several liability through defects-liability period; lists each partner's role and percentage share; signed by all partners.",
                "cited_clauses": ["MAND-JV-AGREEMENT", "MAND-LEAD-POA"],
            },
            {
                "heading": "1.7 Power of Attorney (Form-2)",
                "body": "Notarized Power of Attorney identifying the authorized signatory; notarization not older than 6 months.",
                "cited_clauses": ["MAND-POA"],
            },
            {
                "heading": "1.8 Integrity Pact (Form-13)",
                "body": "Bidder undertakes no use of intermediaries or bribes; signed by the same authorized signatory listed in Form-2.",
                "cited_clauses": ["MAND-INTEGRITY-PACT", "MAND-NO-EXCEPTIONS"],
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
            "STUB MODE — no LLM key available. Officer should review: (a) whether 2% EMD is appropriate "
            "for the contract type, (b) whether the lookback period reflects current corrigenda, (c) special "
            "requirements specific to this project type that may need additional clauses."
        ),
    }


def draft_section_1(db: Session, tender_id: int, brief: dict[str, Any]) -> dict[str, Any]:
    """Generate a Section 1 draft based on a project brief."""
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

    client, model = _client()

    if client is None:
        result = _stub_draft(brief, clauses)
        result["model_version"] = "drafting-stub-v1"
        return result

    # Build the RAG context: mandatory clauses + a slice of the reference Section 1
    clause_library = [
        {"code": c.code, "title": c.title, "section": c.source_section, "text": c.source_text[:400]}
        for c in clauses
    ]
    reference_excerpt = (section_1.raw_text[:8000] if section_1 else "(no reference Section 1 available)")

    user_prompt = f"""PROJECT BRIEF:
{json.dumps(brief, indent=2)}

MANDATORY CLAUSE LIBRARY (cite by code):
{json.dumps(clause_library, indent=2)}

REFERENCE SECTION 1 EXCERPT (for tone + structure inspiration):
\"\"\"
{reference_excerpt}
\"\"\"

Generate the draft Section 1 (ITT) JSON now.
"""

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = resp.content[0].text  # type: ignore[attr-defined]
        # Strip any accidental fences
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1] if "```" in text[3:] else text[3:]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0]
        result = json.loads(text)
        result["model_version"] = f"drafting-{model}"
        return result
    except json.JSONDecodeError as e:
        # LLM returned malformed/truncated JSON — fall back to stub but keep the model name visible.
        result = _stub_draft(brief, clauses)
        result["model_version"] = f"drafting-{model}-stub-fallback (parse error)"
        result["ai_notes"] = (
            f"LLM response could not be parsed (JSON error at char {e.pos}). "
            f"Falling back to deterministic template. In production, the system would retry with stricter prompting "
            f"or split the request into per-section calls."
        ) + " " + result.get("ai_notes", "")
        return result
    except Exception as e:  # noqa: BLE001
        result = _stub_draft(brief, clauses)
        result["model_version"] = f"drafting-stub-after-error: {e}"
        return result
