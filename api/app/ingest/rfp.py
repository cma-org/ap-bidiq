"""RFP and Corrigendum ingestion → versioned ActiveRules.

Strategy:
 1. Walk the corpus dir; classify each file into a standard EPCC section.
 2. Persist sections + corrigenda raw text.
 3. Run a clause/threshold extractor to build a structured ActiveRules JSON v1
    (pre-corrigendum baseline).
 4. Apply each corrigendum's patches to produce v2, v3, ... (post-corrigendum
    effective rules).
 5. Each version stored separately so the UI can show diffs.

For the demo we use a *deterministic + curated* extractor seeded with knowledge
of the EPCC Fishing Harbour package. This avoids LLM cost on the static corpus
and is reproducible. The LLM layer is reserved for vendor-bid clause semantics.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.ingest.docs import extract_text
from app.models import (
    ActiveRules,
    Corrigendum,
    FormRequired,
    MandatoryClause,
    Patch,
    Section,
    Tender,
)


# ---- Section classification ------------------------------------------------

SECTION_MAP: dict[str, tuple[int, str]] = {
    # filename pattern → (order_idx, canonical name)
    "Tendering Procedure Cover Page": (0, "Cover Page"),
    "Section 1-ITT": (1, "Section 1 — Instructions to Tenderers (ITT)"),
    "Section 2-TDS": (2, "Section 2 — Tender Data Sheet (TDS)"),
    "Section 3-QR": (3, "Section 3 — Qualification Requirements (QR)"),
    "Section 4-Tender Forms": (4, "Section 4 — Tender Forms"),
    "Section 5- Schedule of Payments": (5, "Section 5 — Schedule of Payments"),
    "Section - 6A - Scope of Work": (6, "Section 6A — Scope of Work"),
    "Section - 6B - Technical Specifications": (7, "Section 6B — Technical Specifications"),
    "Section - 6C - Design Criteria": (8, "Section 6C — Design Criteria"),
    "Section - 7 General Requirements": (9, "Section 7 — General Requirements"),
    "Section - 8 General Conditions": (10, "Section 8 — General Conditions of Contract"),
    "Section - 9 Special Conditions of Contract": (11, "Section 9 — Special Conditions of Contract"),
    "Section - 10 Contract forms": (12, "Section 10 — Contract Forms"),
    "RFP PMC Fishing Harbours": (13, "Top-Level RFP — PMC Fishing Harbours Phase II + FLCs"),
    "Evaluation Statements": (14, "Evaluation Statements (human evaluator template)"),
}

CORRIGENDUM_PATTERN = re.compile(r"corrigend(um|a)", re.IGNORECASE)


def classify_section(filename: str) -> tuple[int, str] | None:
    base = Path(filename).stem
    # Strip duplicated .docx in our textutil sidecars
    if base.endswith(".docx") or base.endswith(".doc"):
        base = base.rsplit(".", 1)[0]
    for key, (order, canonical) in SECTION_MAP.items():
        if key.lower() in base.lower():
            return order, canonical
    return None


def is_corrigendum(filename: str) -> bool:
    return bool(CORRIGENDUM_PATTERN.search(filename))


# ---- Mandatory clauses + forms (curated seed for the EPCC Fishing Harbour package)

MANDATORY_CLAUSES_SEED: list[dict[str, str]] = [
    {
        "code": "MAND-EMD",
        "title": "Earnest Money Deposit (EMD / Bid Bond) present, valid, correct amount",
        "source_section": "Section 1 — ITT",
        "source_clause": "ITT 1.12",
        "layer": "L1",
        "source_text": "Bid Bond / Earnest Money Deposit shall be furnished as per Form-B for the amount specified in the TDS, valid for 180 days from bid submission.",
    },
    {
        "code": "MAND-DOC-INTEGRITY",
        "title": "Tender Document Integrity declaration (Form-12)",
        "source_section": "Section 4 — Tender Forms",
        "source_clause": "Form-12",
        "layer": "L2",
        "source_text": "Bidder certifies that no alterations have been made to the tender document and signs every page.",
    },
    {
        "code": "MAND-COMPANY-REG",
        "title": "Company Registration certificate",
        "source_section": "Section 1 — ITT",
        "source_clause": "ITT 1.6.2(a)",
        "layer": "L1",
        "source_text": "Scanned copy of Companies Act registration certificate; registered entity name must match the bid signatory.",
    },
    {
        "code": "MAND-EPF-ESI",
        "title": "EPF and ESI registration certificates (current)",
        "source_section": "Section 1 — ITT",
        "source_clause": "ITT 1.6.2(b)",
        "layer": "L1",
        "source_text": "Current EPF and ESI registration certificates in the bidder's name.",
    },
    {
        "code": "MAND-PAN-GST",
        "title": "PAN and GST registration",
        "source_section": "Section 1 — ITT",
        "source_clause": "ITT 1.6.2(c)",
        "layer": "L1",
        "source_text": "Valid PAN and GST registration in the bidder entity name.",
    },
    {
        "code": "MAND-POA",
        "title": "Power of Attorney (notarized, ≤6 months old)",
        "source_section": "Section 4 — Tender Forms",
        "source_clause": "Form-2",
        "layer": "L1+L2",
        "source_text": "Notarized Power of Attorney identifying the authorized signatory; notarization must not be older than 6 months from bid date.",
    },
    {
        "code": "MAND-FIN-3YR",
        "title": "Audited financial statements for last 3 years",
        "source_section": "Section 3 — QR",
        "source_clause": "QR 3.1 / Form-4",
        "layer": "L1",
        "source_text": "Audited Profit & Loss, Balance Sheet, and turnover-from-operations note for each of the last three financial years; must be audited and in the bidder entity's name.",
    },
    {
        "code": "MAND-EXP-CERT",
        "title": "Experience certificates (similar / specialized works)",
        "source_section": "Section 3 — QR",
        "source_clause": "QR 4.1 / Form-5A,5B,5C",
        "layer": "L2",
        "source_text": "For government projects: certificates issued by Executive Engineer countersigned by Superintending Engineer. For private projects: TDS certificate plus CA certificate of client organisation. Must list completion cost and dates.",
    },
    {
        "code": "MAND-EQUIP",
        "title": "Equipment list (Form-8)",
        "source_section": "Section 4 — Tender Forms",
        "source_clause": "Form-8",
        "layer": "L1",
        "source_text": "List of proposed equipment meeting the minimum requirements specified in technical specifications.",
    },
    {
        "code": "MAND-KEY-PERSONNEL",
        "title": "Key personnel statement with CVs (Form-9)",
        "source_section": "Section 4 — Tender Forms",
        "source_clause": "Form-9",
        "layer": "L1",
        "source_text": "Names, qualifications, and years of experience for all proposed key personnel; CVs attached.",
    },
    {
        "code": "MAND-INTEGRITY-PACT",
        "title": "Integrity Pact signed by authorized signatory (Form-13)",
        "source_section": "Section 4 — Tender Forms",
        "source_clause": "Form-13",
        "layer": "L2",
        "source_text": "Bidder undertakes no use of intermediaries or bribes; signed by the same authorized signatory as listed in Form-2.",
    },
    {
        "code": "MAND-JV-AGREEMENT",
        "title": "Joint Venture Agreement with joint and several liability (Form-14)",
        "source_section": "Section 4 — Tender Forms",
        "source_clause": "Form-14 / ITT 1.6.4",
        "layer": "L2",
        "source_text": "If consortium: signed JV agreement establishing joint and several liability through defects-liability period; lists each partner's role and percentage share; signed by all partners.",
    },
    {
        "code": "MAND-LEAD-POA",
        "title": "Power of Attorney for Lead JV Member (Form-15)",
        "source_section": "Section 4 — Tender Forms",
        "source_clause": "Form-15",
        "layer": "L2",
        "source_text": "Notarized PoA from each non-lead JV member granting the lead member authority for all dealings related to this contract.",
    },
    {
        "code": "MAND-NO-EXCEPTIONS",
        "title": "No-exceptions / no-deviations declaration (Form-12)",
        "source_section": "Section 4 — Tender Forms",
        "source_clause": "Form-12",
        "layer": "L2",
        "source_text": "Bidder certifies no deviations from tender; financial bid is unconditional.",
    },
    {
        "code": "MAND-PRICE-SCHEDULE",
        "title": "Bid Form + Price Schedule arithmetic consistency",
        "source_section": "Section 4 + 10",
        "source_clause": "Section 4 / Section 10",
        "layer": "L1",
        "source_text": "Bills 1-5 lump-sum amounts must sum to the Grand Summary total within ±0.1% tolerance; each bill signed and dated.",
    },
]


FORMS_REQUIRED_SEED: list[dict[str, Any]] = [
    {"form_no": "Form-1", "title": "Letter of Submission + Eligibility declaration", "schema": {}},
    {"form_no": "Form-2", "title": "Power of Attorney (notarized)", "schema": {"signatory_name": "str", "notary_date": "date", "scope": "str"}},
    {"form_no": "Form-3", "title": "Organization Details", "schema": {"company_name": "str", "registration_no": "str", "address": "str", "pan": "str", "gst": "str"}},
    {"form_no": "Form-4", "title": "Annual Financial Turnover (3 years)", "schema": {"turnover_year_1_inr_cr": "float", "turnover_year_2_inr_cr": "float", "turnover_year_3_inr_cr": "float"}},
    {"form_no": "Form-5A", "title": "Similar Work Experience", "schema": {"projects": "list[{name, value_inr_cr, client, completion_date}]"}},
    {"form_no": "Form-5B", "title": "Experience Summary", "schema": {"total_value_inr_cr": "float", "project_count": "int"}},
    {"form_no": "Form-5C", "title": "Specialized Works (breakwater, dredging, piling)", "schema": {"breakwater_rmt": "float", "dredging_cum": "float", "piling": "list[{diameter_mm, length_rmt}]"}},
    {"form_no": "Form-6A", "title": "Available Bid Capacity & Net Worth", "schema": {"max_annual_value_inr_cr": "float", "lookback_years": "int", "ongoing_commitments_inr_cr": "float", "contract_duration_years": "float", "net_worth_inr_cr": "float"}},
    {"form_no": "Form-6B", "title": "Financial Soundness", "schema": {}},
    {"form_no": "Form-7", "title": "Proposed Approach & Methodology", "schema": {"narrative": "str"}},
    {"form_no": "Form-8", "title": "Equipment List", "schema": {"items": "list[{type, qty, ownership}]"}},
    {"form_no": "Form-9", "title": "Key Personnel + CVs", "schema": {"personnel": "list[{role, name, qualification, years}]"}},
    {"form_no": "Form-10", "title": "Proposed Site Organization", "schema": {}},
    {"form_no": "Form-12", "title": "Declarations (no deviations / no intermediaries)", "schema": {"signed": "bool", "signatory_name": "str"}},
    {"form_no": "Form-13", "title": "Integrity Pact", "schema": {"signed": "bool", "signatory_name": "str"}},
    {"form_no": "Form-14", "title": "Joint Bidding (JV) Agreement", "schema": {"jv_entity_name": "str", "partners": "list[{name, share_pct, lead}]", "joint_and_several": "bool"}},
    {"form_no": "Form-15", "title": "Power of Attorney for Lead JV Member", "schema": {}},
    {"form_no": "Form-16", "title": "Letter of Authority", "schema": {}},
    {"form_no": "Form-19", "title": "Bid Submission Checklist", "schema": {"items_present": "list[str]", "items_missing": "list[str]"}},
    {"form_no": "Form-B", "title": "Bid Bond / EMD (Bank Guarantee)", "schema": {"amount_inr_cr": "float", "issuer_bank": "str", "payee_name": "str", "validity_days": "int"}},
    {"form_no": "Form-C", "title": "Performance Security (Bank Guarantee)", "schema": {"amount_inr_cr": "float", "validity_end_date": "date"}},
]


# ---- Active-rules baseline (pre-corrigendum) ------------------------------

def baseline_active_rules() -> dict[str, Any]:
    """The pre-corrigendum effective ruleset extracted from the EPCC TDS + ITT."""
    return {
        "thresholds": {
            "annual_turnover_min_inr_cr": 350.0,                # any 1 yr in last 7 yrs
            "annual_turnover_lookback_years": 7,
            "similar_work_min_inr_cr": 175.0,                   # any 1 yr in last 5 yrs
            "similar_work_lookback_years": 5,
            "specialized_breakwater_rmt_min": 800.0,
            "specialized_dredging_cum_min": 250000.0,
            "specialized_piling_diameter_mm_min": 1000,
            "specialized_piling_length_rmt_min": 300.0,
            "solvency_min_inr_cr": 100.0,
            "solvency_max_age_months": 6,
            "emd_validity_min_days": 180,
            "performance_security_pct": 10.0,
            "performance_security_dlp_buffer_days": 90,
        },
        "bid_capacity_formula": {
            "expression": "(A * N * 3) - B",
            "A_definition": "Max annual contract value executed in any year of the lookback window",
            "A_lookback_years": 5,                              # ← changed by Corrigendum-1
            "N_definition": "Duration of current contract in years",
            "B_definition": "Value of existing commitments and ongoing works to complete in next N years",
            "pass_rule": "available_bid_capacity >= submitted_bid_value",
        },
        "evaluation_method": {
            "stage_1": "Qualification — pass/fail on all mandatory + threshold checks",
            "stage_2": "Financial bid — L1 (lowest evaluated bid) wins",
        },
        "subcontractor_rule": {
            "max_specialized_subcontractors": 3,
            "max_subcontractor_value_pct": 50.0,
        },
        "extras_protocol": None,  # ← added by Corrigendum-1
    }


# ---- Corrigendum patch detection ------------------------------------------

def detect_patches(corrigendum_text: str) -> list[dict[str, Any]]:
    """Curated patch detection for Corrigendum-1 (real text we received).

    The corrigendum uses a "For ... Read ..." structure: the "For" column shows
    the original text, the "Read" column shows the replacement. Detection
    matches the actual phrasing in this corpus's Corrigendum-1.

    A future LLM-based extractor would generalize this. For the demo we ship
    a deterministic version that mirrors the actual changes in the file.
    """
    patches: list[dict[str, Any]] = []
    text_lc = corrigendum_text.lower()

    # Bid capacity lookback: "last Five years" replaced with "last Ten years"
    if "last five  years" in text_lc and "last ten years" in text_lc and "bid capacity" in text_lc:
        patches.append({
            "target_clause": "ITT 1.6.1 — Available Bid Capacity (Financial Capacity B(2))",
            "op": "threshold_update",
            "before": "‘A’ = maximum value of works executed in any one year during last Five years (at current price level).",
            "after": "‘A’ = maximum value of works executed in any one year during last Ten years (at current price level).",
            "summary": "Available Bid Capacity lookback extended from 5 → 10 years. Disqualifies bidders relying on capacity from years 6-10 ago.",
            "applies_to": {"bid_capacity_formula.A_lookback_years": 10},
        })

    # Extra items protocol — added in clause 40.1+ with new threshold/timing rules
    if "extra items" in text_lc and "40.1" in text_lc:
        patches.append({
            "target_clause": "GCC 40 — Extra Items Protocol",
            "op": "append",
            "before": None,
            "after": "Detailed protocol added: 10% threshold, monthly statement before 15th of following month, Committee approval required for >10% deviations.",
            "summary": "Extra-items procedure formalised: 10% threshold, monthly cycle, Committee review for excursions.",
            "applies_to": {
                "extras_protocol": {
                    "deviation_threshold_pct": 10.0,
                    "monthly_statement_due_day_of_next_month": 15,
                    "committee_approval_required_above_pct": 10.0,
                }
            },
        })

    return patches


def apply_patches(rules: dict[str, Any], patches: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply structured patches to an ActiveRules dict (deep merge by path)."""
    import copy
    out = copy.deepcopy(rules)
    for p in patches:
        for path, value in p.get("applies_to", {}).items():
            _set_path(out, path, value)
    return out


def _set_path(obj: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = obj
    for k in parts[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    last = parts[-1]
    if isinstance(value, dict) and isinstance(cur.get(last), dict):
        cur[last].update(value)
    else:
        cur[last] = value


# ---- Top-level ingest -----------------------------------------------------

@dataclass
class IngestReport:
    tender_id: int
    sections_loaded: int = 0
    corrigenda_loaded: int = 0
    patches_detected: int = 0
    active_rule_versions: list[int] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def ingest_corpus(
    db: Session,
    corpus_dir: Path,
    *,
    title: str = "EPCC Fishing Harbours Phase II",
    department: str = "Infrastructure & Investment Department, Government of Andhra Pradesh",
    code: str = "EPCC-FH-PII-2025",
) -> IngestReport:
    """Idempotent ingest. Re-uses existing tender row (preserves ID) and clears sub-rows."""
    from app.models import (
        ActiveRules,
        Corrigendum,
        FormRequired,
        MandatoryClause,
        Section,
    )

    tender = db.query(Tender).filter(Tender.code == code).first()
    if tender:
        # Clear children but keep the row so the tender_id stays stable.
        db.query(Section).filter(Section.tender_id == tender.id).delete()
        db.query(Corrigendum).filter(Corrigendum.tender_id == tender.id).delete()
        db.query(MandatoryClause).filter(MandatoryClause.tender_id == tender.id).delete()
        db.query(FormRequired).filter(FormRequired.tender_id == tender.id).delete()
        db.query(ActiveRules).filter(ActiveRules.tender_id == tender.id).delete()
        # title/department may have been edited — restore to canonical
        tender.title = title
        tender.department = department
        db.commit()
    else:
        tender = Tender(title=title, department=department, code=code)
        db.add(tender)
        db.flush()

    report = IngestReport(tender_id=tender.id)

    # 1) Sections + corrigenda
    for path in sorted(corpus_dir.iterdir()):
        if path.is_dir() or path.name.startswith(".") or path.name.endswith(".txt"):
            continue
        text = extract_text(path)
        if is_corrigendum(path.name):
            c = Corrigendum(
                tender_id=tender.id,
                name=path.stem,
                order_idx=len(tender.corrigenda) + 1,
                raw_text=text,
            )
            db.add(c)
            db.flush()
            patches = detect_patches(text)
            for p in patches:
                db.add(Patch(
                    corrigendum_id=c.id,
                    target_clause=p["target_clause"],
                    op=p["op"],
                    before_text=p.get("before"),
                    after_text=p.get("after"),
                    semantic_summary=p.get("summary"),
                ))
            report.corrigenda_loaded += 1
            report.patches_detected += len(patches)
        else:
            classified = classify_section(path.name)
            if classified is None:
                report.notes.append(f"unclassified file: {path.name}")
                continue
            order_idx, canonical = classified
            db.add(Section(
                tender_id=tender.id,
                name=canonical,
                order_idx=order_idx,
                raw_text=text,
                source_path=str(path),
            ))
            report.sections_loaded += 1

    # 2) Mandatory clauses + forms (from curated seed)
    for mc in MANDATORY_CLAUSES_SEED:
        db.add(MandatoryClause(
            tender_id=tender.id,
            code=mc["code"],
            title=mc["title"],
            source_section=mc["source_section"],
            source_text=mc["source_text"],
            layer=mc["layer"],
        ))
    for f in FORMS_REQUIRED_SEED:
        db.add(FormRequired(
            tender_id=tender.id,
            form_no=f["form_no"],
            title=f["title"],
            schema=f["schema"],
        ))

    # 3) Active rules: v1 = baseline; v2 = baseline + Corrigendum-1
    baseline = baseline_active_rules()
    db.add(ActiveRules(tender_id=tender.id, version=1, payload=baseline))
    report.active_rule_versions.append(1)

    db.flush()  # so we can query corrigenda
    all_patches: list[dict[str, Any]] = []
    for c in db.query(Corrigendum).filter(Corrigendum.tender_id == tender.id).order_by(Corrigendum.order_idx).all():
        all_patches.extend(detect_patches(c.raw_text))
    if all_patches:
        v2 = apply_patches(baseline, all_patches)
        db.add(ActiveRules(tender_id=tender.id, version=2, payload=v2))
        report.active_rule_versions.append(2)

    db.commit()
    return report
