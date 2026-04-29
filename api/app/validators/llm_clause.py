"""Layer-2 LLM clause-semantics validator.

Uses an LLM (default: GPT-4o) to verify clause-level requirements that need
text understanding, not just field comparison. Every finding includes a
quoted source citation that the officer can verify in 5 seconds.

PII (vendor names, PAN, GST, signatory names, contact info) is redacted from
bid data before it leaves the boundary. The redaction count is surfaced in
the finding so the audit trail records 'N PII tokens masked'.

Falls back to deterministic stubs when no API key is set, so the demo runs
even offline.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Bid, FormExtraction, MandatoryClause, Validation
from app.services.llm import LLMUnavailable, chat_json, get_strong_model_label, is_available
from app.services.redact import redact_for_llm_call
from app.validators.deterministic import Finding, _by_form, _ok, _fail


SYSTEM_PROMPT = """You are an expert evaluator of public-procurement bids for the Government of Andhra Pradesh.

You will be given:
1. Excerpts of mandatory clauses from the tender document (the "active rules").
2. The relevant extracted fields from a vendor's bid submission (with PII redacted).

Your job is to evaluate ONE specific compliance check and return a JSON object with:
- verdict: "pass" | "fail" | "warning"
- message: brief explanation (≤ 200 chars)
- citation_text: an EXACT quoted phrase from the source clause that justifies your verdict (≤ 200 chars)
- evidence_summary: brief description of what the bid showed (≤ 200 chars)

Be conservative. If the bid demonstrably meets the requirement, pass. If a required element is missing or contradicts the rule, fail. If you're unsure, return warning with a clear explanation. Output JSON only.
"""


# ---- Stub fallbacks (run when no API key) --------------------------------

def _stub_integrity_pact(forms: dict, mc: MandatoryClause | None) -> Finding:
    f13 = forms.get("Form-13", {})
    f12 = forms.get("Form-12", {})
    if not f13.get("signed"):
        return _fail("FR-VAL-2.1", "Integrity Pact signed", "Form-13 not signed.",
                     citation_section="Section 4 — Tender Forms", citation_clause="Form-13",
                     citation_text="Bidder undertakes no use of intermediaries or bribes; signed by the same authorized signatory as listed in Form-2.")
    f13_signer = f13.get("signatory_name", "")
    f12_signer = f12.get("signatory_name", "") if f12 else ""
    if f13_signer and f12_signer and f13_signer != f12_signer:
        return _fail(
            "FR-VAL-2.1", "Integrity Pact signed by authorised signatory",
            f"Form-13 signed by '{f13_signer}' but Form-12 declarations signed by '{f12_signer}'. Same authorised signatory required.",
            citation_section="Section 4 — Tender Forms", citation_clause="Form-13 + Form-2",
            citation_text="Integrity Pact must be signed by the same authorised signatory listed in Form-2 PoA.",
        )
    return _ok(
        "FR-VAL-2.1", "Integrity Pact signed by authorised signatory",
        f"Form-13 signed by {f13_signer or '(declared signatory)'} — matches PoA designate.",
        citation_section="Section 4 — Tender Forms", citation_clause="Form-13",
        citation_text="Bidder undertakes no use of intermediaries or bribes; signed by the same authorized signatory as listed in Form-2.",
    )


def _stub_jv_joint_several(forms: dict, mc: MandatoryClause | None) -> Finding:
    f14 = forms.get("Form-14", {})
    if not f14:
        return _ok("FR-VAL-2.2", "JV joint-and-several liability", "Single-entity bidder — JV check not applicable.")
    if not f14.get("joint_and_several"):
        return _fail("FR-VAL-2.2", "JV joint-and-several liability",
                     "Form-14 does not assert joint and several liability of all partners.",
                     citation_section="Section 4 — Tender Forms", citation_clause="Form-14 / ITT 1.6.4",
                     citation_text="Joint Venture Agreement establishing joint and several liability through defects-liability period; lists each partner's role and percentage share; signed by all partners.")
    partners = f14.get("partners", [])
    total_share = sum(p.get("share_pct", 0) for p in partners)
    if abs(total_share - 100.0) > 0.5:
        return _fail("FR-VAL-2.2", "JV joint-and-several liability",
                     f"JV partner shares sum to {total_share}% (must equal 100%).",
                     citation_section="Section 4 — Tender Forms", citation_clause="Form-14",
                     citation_text="Lists each partner's role and percentage share; signed by all partners.")
    return _ok("FR-VAL-2.2", "JV joint-and-several liability",
               f"JV agreement asserts joint and several liability across {len(partners)} partner(s) summing to {total_share}%.",
               citation_section="Section 4 — Tender Forms", citation_clause="Form-14",
               citation_text="Joint Venture Agreement establishing joint and several liability through defects-liability period.")


def _stub_no_exceptions(forms: dict, mc: MandatoryClause | None) -> Finding:
    f12 = forms.get("Form-12", {})
    if not f12.get("signed") or not f12.get("no_deviations") or not f12.get("no_intermediaries"):
        return _fail("FR-VAL-2.4", "No-exceptions / no-deviations declaration",
                     "Form-12 is not signed or does not certify no deviations / no intermediaries.",
                     citation_section="Section 4 — Tender Forms", citation_clause="Form-12",
                     citation_text="Bidder certifies no deviations from tender; financial bid is unconditional.")
    return _ok("FR-VAL-2.4", "No-exceptions / no-deviations declaration",
               "Form-12 declarations are signed and clear.",
               citation_section="Section 4 — Tender Forms", citation_clause="Form-12",
               citation_text="Bidder certifies no deviations from tender; financial bid is unconditional.")


# ---- LLM-driven validators ----------------------------------------------

def _llm_check(*, check_id: str, title: str,
               clause_text: str, bid_excerpt: dict, source_section: str, source_clause: str,
               vendor_names: list[str] | None = None) -> Finding:
    """Make one LLM call for one compliance check, with PII redaction."""
    redacted_json, redaction_report = redact_for_llm_call(bid_excerpt, vendor_names or [])

    user_prompt = f"""Compliance check: {title}

Mandatory clause from tender:
\"\"\"
{clause_text}
\"\"\"

Source: {source_section} / {source_clause}

Vendor bid excerpts (JSON, PII redacted):
{redacted_json}

Decide if the bid satisfies this clause. Output JSON only:
{{"verdict": "...", "message": "...", "citation_text": "...", "evidence_summary": "..."}}"""

    try:
        parsed = chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=400,
            temperature=0.0,
        )
    except (LLMUnavailable, ValueError, Exception) as e:  # noqa: BLE001
        return _fail(check_id, title, f"LLM check failed: {type(e).__name__}", severity="info",
                     citation_section=source_section, citation_clause=source_clause,
                     citation_text=clause_text[:200])

    verdict = parsed.get("verdict", "warning")
    message = parsed.get("message", "(no message)")
    citation_text = parsed.get("citation_text", clause_text[:200])
    if redaction_report.total > 0:
        message = f"{message} (PII masked before LLM call: {redaction_report.total} tokens — {dict(redaction_report.counts_by_type)})"
    if verdict == "pass":
        return _ok(check_id, title, message,
                   citation_section=source_section, citation_clause=source_clause,
                   citation_text=citation_text)
    return _fail(check_id, title, message, severity="major" if verdict == "fail" else "minor",
                 citation_section=source_section, citation_clause=source_clause,
                 citation_text=citation_text)


def run_llm_validators(db: Session, bid_id: int) -> tuple[list[Finding], str]:
    """Returns (findings, model_version). Falls back to stubs without an LLM key."""
    bid = db.get(Bid, bid_id)
    if bid is None:
        raise ValueError(f"bid {bid_id} not found")

    forms = _by_form(bid.extractions)
    mcs = {m.code: m for m in db.query(MandatoryClause).filter(MandatoryClause.tender_id == bid.tender_id).all()}

    if not is_available():
        findings = [
            _stub_integrity_pact(forms, mcs.get("MAND-INTEGRITY-PACT")),
            _stub_jv_joint_several(forms, mcs.get("MAND-JV-AGREEMENT")),
            _stub_no_exceptions(forms, mcs.get("MAND-NO-EXCEPTIONS")),
        ]
        return findings, "llm-stub-v1"

    findings: list[Finding] = []
    vendor_names = [bid.vendor_name] + (bid.jv_partners or [])

    # Check 1: Integrity Pact authorised signatory
    mc = mcs.get("MAND-INTEGRITY-PACT")
    if mc:
        findings.append(_llm_check(
            check_id="FR-VAL-2.1",
            title="Integrity Pact signed by authorised signatory",
            clause_text=mc.source_text,
            bid_excerpt={"Form-13": forms.get("Form-13", {}), "Form-12": forms.get("Form-12", {}), "Form-2_signatory": forms.get("Form-2", {}).get("signatory_name") if forms.get("Form-2") else None},
            source_section=mc.source_section, source_clause="Form-13",
            vendor_names=vendor_names,
        ))

    # Check 2: JV joint-and-several
    mc = mcs.get("MAND-JV-AGREEMENT")
    if mc and forms.get("Form-14"):
        findings.append(_llm_check(
            check_id="FR-VAL-2.2",
            title="JV joint-and-several liability + share split",
            clause_text=mc.source_text,
            bid_excerpt={"Form-14": forms.get("Form-14", {})},
            source_section=mc.source_section, source_clause="Form-14",
            vendor_names=vendor_names,
        ))

    # Check 3: No-exceptions declaration
    mc = mcs.get("MAND-NO-EXCEPTIONS")
    if mc:
        findings.append(_llm_check(
            check_id="FR-VAL-2.4",
            title="No-exceptions / no-deviations declaration",
            clause_text=mc.source_text,
            bid_excerpt={"Form-12": forms.get("Form-12", {})},
            source_section=mc.source_section, source_clause="Form-12",
            vendor_names=vendor_names,
        ))

    return findings, f"llm-{get_strong_model_label()}"


def persist_llm_findings(db: Session, bid_id: int, findings: list[Finding], model_version: str) -> int:
    db.query(Validation).filter(Validation.bid_id == bid_id, Validation.layer == "L2").delete()
    db.commit()
    for f in findings:
        db.add(Validation(
            bid_id=bid_id,
            check_id=f.check_id,
            layer="L2",
            verdict=f.verdict,
            severity=f.severity,
            title=f.title,
            message=f.message,
            citation_section=f.citation_section,
            citation_clause=f.citation_clause,
            citation_text=f.citation_text,
            evidence={},
            model_version=model_version,
        ))
    db.commit()
    return len(findings)
