"""Synthetic vendor bids for the EPCC Fishing Harbours Phase II demo.

Each bid is structured as the form-extraction JSON we'd get out of a real
PDF/DOCX upload — Form-3 (org), Form-4 (turnover), Form-5A/5C (experience),
Form-6A (bid capacity), Form-14 (JV agreement), Form-19 (checklist), Form-B
(EMD/Bid Bond), plus declarations.

Bid 01 is fully compliant. Bids 02-05 each plant 1-2 specific defects so we
can verify accuracy against ground-truth labels.

Vendor names are based on actual large Indian infra contractors who plausibly
bid for AP marine works, to make the demo feel real to government judges.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Bid, FormExtraction


BID_DATE = date(2026, 4, 25)  # the day bids are evaluated in the demo


# Estimated bid value in INR Cr — used to test bid capacity formula
DEMO_BID_VALUE_CR = 380.0
DEMO_CONTRACT_DURATION_YEARS = 3.0


def _form19_checklist(items_present: list[str], items_missing: list[str]) -> dict[str, Any]:
    return {"items_present": items_present, "items_missing": items_missing}


def _form2(signatory_name: str, scope: str = "Authorised to sign and submit the bid, execute the contract, and represent the bidder in all dealings with the Employer.") -> dict[str, Any]:
    return {
        "signatory_name": signatory_name,
        "notary_date": (BID_DATE - timedelta(days=45)).isoformat(),
        "scope": scope,
        "notarised": True,
    }


def _bid_bond(payee: str, amount_cr: float = 7.6, valid_days: int = 210, issuer: str = "State Bank of India") -> dict[str, Any]:
    return {
        "amount_inr_cr": amount_cr,
        "issuer_bank": issuer,
        "payee_name": payee,
        "validity_days": valid_days,
        "issue_date": (BID_DATE - timedelta(days=15)).isoformat(),
        "validity_end_date": (BID_DATE + timedelta(days=valid_days - 15)).isoformat(),
    }


# ---- BID 01 — CLEAN -------------------------------------------------------

BID_01_CLEAN: dict[str, Any] = {
    "vendor_name": "Megha Engineering & Infrastructures Ltd. (MEIL)",
    "jv_partners": ["Megha Engineering & Infrastructures Ltd."],
    "bid_value_inr_cr": DEMO_BID_VALUE_CR,
    "submitted_at_iso": BID_DATE.isoformat(),
    "label": {
        "verdict": "Qualified",
        "expected_findings": [],
        "narrative": "Fully compliant baseline bid.",
    },
    "extractions": {
        "Form-3": {
            "company_name": "Megha Engineering & Infrastructures Ltd.",
            "registration_no": "U45200TG2006PLC050347",
            "address": "Megha House, Hyderabad, Telangana",
            "pan": "AABCM4567K",
            "gst": "36AABCM4567K1Z3",
        },
        "Form-4": {
            "turnover_year_1_inr_cr": 12450.0,
            "turnover_year_2_inr_cr": 9870.0,
            "turnover_year_3_inr_cr": 8210.0,
            "best_year_inr_cr": 12450.0,
            "best_year_label": "FY 2024-25",
        },
        "Form-5A": {
            "projects": [
                {"name": "Dhamra Port Breakwater Extension", "value_inr_cr": 412.0, "client": "Dhamra Port Co. Ltd.", "completion_date": "2024-08-31"},
                {"name": "Vizhinjam Container Terminal Marine Works", "value_inr_cr": 285.0, "client": "Adani Vizhinjam Port Pvt Ltd", "completion_date": "2023-11-15"},
                {"name": "Krishnapatnam Coal Berth Construction", "value_inr_cr": 198.0, "client": "Krishnapatnam Port Co.", "completion_date": "2022-06-30"},
            ],
        },
        "Form-5C": {
            "breakwater_rmt": 1250.0,
            "dredging_cum": 480000.0,
            "piling": [{"diameter_mm": 1200, "length_rmt": 520.0}],
        },
        "Form-6A": {
            "max_annual_value_inr_cr": 412.0,
            "lookback_years": 10,
            "ongoing_commitments_inr_cr": 380.0,
            "contract_duration_years": DEMO_CONTRACT_DURATION_YEARS,
            "net_worth_inr_cr": 2840.0,
            "solvency_inr_cr": 600.0,
            "solvency_cert_date": (BID_DATE - timedelta(days=120)).isoformat(),
        },
        "Form-2": _form2("P. Pitchi Reddy"),
        "Form-12": {"signed": True, "signatory_name": "P. Pitchi Reddy", "no_deviations": True, "no_intermediaries": True},
        "Form-13": {"signed": True, "signatory_name": "P. Pitchi Reddy"},
        "Form-14": {
            "jv_entity_name": "Megha Engineering & Infrastructures Ltd.",
            "partners": [{"name": "Megha Engineering & Infrastructures Ltd.", "share_pct": 100.0, "lead": True}],
            "joint_and_several": True,
        },
        "Form-19": _form19_checklist(
            items_present=[
                "Form-1 Letter of Submission", "Form-2 Power of Attorney", "Form-3 Org Details",
                "Form-4 Turnover", "Form-5A Similar Work", "Form-5C Specialized Works",
                "Form-6A Bid Capacity", "Form-7 Methodology", "Form-8 Equipment", "Form-9 Personnel",
                "Form-12 Declarations", "Form-13 Integrity Pact", "Form-14 JV Agreement", "Form-19 Checklist",
                "Form-B Bid Bond", "EPF Cert", "ESI Cert", "PAN", "GST", "Solvency Cert",
                "Audited Financials Y1", "Audited Financials Y2", "Audited Financials Y3",
            ],
            items_missing=[],
        ),
        "Form-B": _bid_bond(payee="Megha Engineering & Infrastructures Ltd."),
        "Bills": {"bill_1_inr_cr": 95.0, "bill_2_inr_cr": 110.0, "bill_3_inr_cr": 78.0, "bill_4_inr_cr": 52.0, "bill_5_inr_cr": 45.0, "grand_summary_inr_cr": 380.0},
    },
}


# ---- BID 02 — Missing Bid Bond ------------------------------------------

BID_02_MISSING_BG: dict[str, Any] = {
    "vendor_name": "L&T Construction (Heavy Civil Infrastructure)",
    "jv_partners": ["Larsen & Toubro Limited"],
    "bid_value_inr_cr": 388.5,
    "submitted_at_iso": BID_DATE.isoformat(),
    "label": {
        "verdict": "Not Qualified",
        "expected_findings": ["FR-VAL-1.1", "FR-VAL-1.2"],
        "narrative": "Form-19 ticked the Bid Bond as present, but the BG document itself is absent. Auto-reject under ITT 1.6.2.",
    },
    "extractions": {
        "Form-3": {
            "company_name": "Larsen & Toubro Limited",
            "registration_no": "L99999MH1946PLC004768",
            "address": "L&T House, Mumbai, Maharashtra",
            "pan": "AAACL0140P",
            "gst": "27AAACL0140P1Z3",
        },
        "Form-4": {
            "turnover_year_1_inr_cr": 24560.0,
            "turnover_year_2_inr_cr": 21340.0,
            "turnover_year_3_inr_cr": 19870.0,
            "best_year_inr_cr": 24560.0,
        },
        "Form-5A": {
            "projects": [
                {"name": "Kattupalli Port Phase 2 Marine Works", "value_inr_cr": 528.0, "client": "Marine Infrastructure Developer Pvt Ltd", "completion_date": "2024-03-20"},
                {"name": "Mundra Port LPG Terminal", "value_inr_cr": 312.0, "client": "Mundra LPG Pvt Ltd", "completion_date": "2023-09-10"},
            ],
        },
        "Form-5C": {
            "breakwater_rmt": 2100.0,
            "dredging_cum": 720000.0,
            "piling": [{"diameter_mm": 1500, "length_rmt": 890.0}],
        },
        "Form-6A": {
            "max_annual_value_inr_cr": 528.0,
            "lookback_years": 10,
            "ongoing_commitments_inr_cr": 1200.0,
            "contract_duration_years": DEMO_CONTRACT_DURATION_YEARS,
            "net_worth_inr_cr": 18500.0,
            "solvency_inr_cr": 2000.0,
            "solvency_cert_date": (BID_DATE - timedelta(days=60)).isoformat(),
        },
        "Form-2": _form2("S.N. Subrahmanyan"),
        "Form-12": {"signed": True, "signatory_name": "S.N. Subrahmanyan", "no_deviations": True, "no_intermediaries": True},
        "Form-13": {"signed": True, "signatory_name": "S.N. Subrahmanyan"},
        "Form-14": {
            "jv_entity_name": "Larsen & Toubro Limited",
            "partners": [{"name": "Larsen & Toubro Limited", "share_pct": 100.0, "lead": True}],
            "joint_and_several": True,
        },
        "Form-19": _form19_checklist(
            items_present=[
                "Form-1", "Form-2", "Form-3", "Form-4", "Form-5A", "Form-5C", "Form-6A",
                "Form-12", "Form-13", "Form-14", "Form-19",
                "Form-B Bid Bond",  # claimed as present but actually missing
                "EPF Cert", "ESI Cert", "PAN", "GST", "Solvency Cert",
                "Audited Financials Y1", "Audited Financials Y2", "Audited Financials Y3",
            ],
            items_missing=[],
        ),
        # Form-B intentionally absent → triggers FR-VAL-1.1 (form missing) + FR-VAL-1.2 (EMD)
        "Bills": {"bill_1_inr_cr": 95.0, "bill_2_inr_cr": 110.0, "bill_3_inr_cr": 78.0, "bill_4_inr_cr": 52.0, "bill_5_inr_cr": 45.0, "grand_summary_inr_cr": 380.0},
    },
}


# ---- BID 03 — BG Name Mismatch (JV-vs-individual-partner) ---------------

BID_03_BG_NAME_MISMATCH: dict[str, Any] = {
    "vendor_name": "Afcons-Tata Projects JV",
    "jv_partners": ["Afcons Infrastructure Ltd.", "Tata Projects Limited"],
    "bid_value_inr_cr": 392.1,
    "submitted_at_iso": BID_DATE.isoformat(),
    "label": {
        "verdict": "Not Qualified",
        "expected_findings": ["FR-VAL-1.3"],
        "narrative": "Bid Bond is issued in the name of Afcons (lead partner) instead of the JV entity. Auto-reject under ITT 1.12 Note.",
    },
    "extractions": {
        "Form-3": {
            "company_name": "Afcons-Tata Projects JV",
            "registration_no": "JV-2025-AFCONS-TATA",
            "address": "c/o Afcons Infrastructure Ltd., Mumbai",
            "pan": "AABCA1234F",
            "gst": "27AABCA1234F1ZA",
        },
        "Form-4": {
            "turnover_year_1_inr_cr": 11200.0,
            "turnover_year_2_inr_cr": 9450.0,
            "turnover_year_3_inr_cr": 8980.0,
            "best_year_inr_cr": 11200.0,
        },
        "Form-5A": {
            "projects": [
                {"name": "JNPT Container Terminal Berth Construction", "value_inr_cr": 420.0, "client": "Jawaharlal Nehru Port Trust", "completion_date": "2024-01-15"},
                {"name": "Cochin Shipyard Dry Dock Works", "value_inr_cr": 235.0, "client": "Cochin Shipyard Limited", "completion_date": "2023-05-22"},
            ],
        },
        "Form-5C": {
            "breakwater_rmt": 1450.0,
            "dredging_cum": 510000.0,
            "piling": [{"diameter_mm": 1200, "length_rmt": 680.0}],
        },
        "Form-6A": {
            "max_annual_value_inr_cr": 420.0,
            "lookback_years": 10,
            "ongoing_commitments_inr_cr": 540.0,
            "contract_duration_years": DEMO_CONTRACT_DURATION_YEARS,
            "net_worth_inr_cr": 6720.0,
            "solvency_inr_cr": 800.0,
            "solvency_cert_date": (BID_DATE - timedelta(days=90)).isoformat(),
        },
        "Form-2": _form2("Subramanian Krishnamurthy"),
        "Form-12": {"signed": True, "signatory_name": "Subramanian Krishnamurthy", "no_deviations": True, "no_intermediaries": True},
        "Form-13": {"signed": True, "signatory_name": "Subramanian Krishnamurthy"},
        "Form-14": {
            "jv_entity_name": "Afcons-Tata Projects JV",
            "partners": [
                {"name": "Afcons Infrastructure Ltd.", "share_pct": 60.0, "lead": True, "role": "Lead — Marine works, breakwater design and execution", "signed": True},
                {"name": "Tata Projects Limited", "share_pct": 40.0, "lead": False, "role": "Onshore civil works, jetty superstructure, utilities", "signed": True},
            ],
            "joint_and_several": True,
            "all_partners_signed": True,
            "valid_through_dlp": True,
        },
        "Form-19": _form19_checklist(
            items_present=[
                "Form-1", "Form-2", "Form-3", "Form-4", "Form-5A", "Form-5C", "Form-6A",
                "Form-12", "Form-13", "Form-14", "Form-15", "Form-19", "Form-B Bid Bond",
                "EPF Cert", "ESI Cert", "PAN", "GST", "Solvency Cert",
                "Audited Financials Y1", "Audited Financials Y2", "Audited Financials Y3",
            ],
            items_missing=[],
        ),
        # The defect: BG payee is "Afcons Infrastructure Ltd." but JV entity is "Afcons-Tata Projects JV"
        "Form-B": _bid_bond(payee="Afcons Infrastructure Ltd."),
        "Bills": {"bill_1_inr_cr": 95.0, "bill_2_inr_cr": 110.0, "bill_3_inr_cr": 78.0, "bill_4_inr_cr": 52.0, "bill_5_inr_cr": 45.0, "grand_summary_inr_cr": 380.0},
    },
}


# ---- BID 04 — Bid Capacity Shortfall ------------------------------------

BID_04_CAPACITY_SHORTFALL: dict[str, Any] = {
    "vendor_name": "Navayuga Engineering Company Ltd.",
    "jv_partners": ["Navayuga Engineering Company Ltd."],
    "bid_value_inr_cr": 376.2,
    "submitted_at_iso": BID_DATE.isoformat(),
    "label": {
        "verdict": "Not Qualified",
        "expected_findings": ["FR-VAL-1.5"],
        "narrative": "Available Bid Capacity = (45 * 3 * 3) - 280 = 125 Cr, which is < bid value 380 Cr. Disqualified under ITT 1.6.1.",
    },
    "extractions": {
        "Form-3": {
            "company_name": "Navayuga Engineering Company Ltd.",
            "registration_no": "U45201TG1986PLC006789",
            "address": "Navayuga House, Hyderabad, Telangana",
            "pan": "AABCN3456J",
            "gst": "36AABCN3456J1Z2",
        },
        "Form-4": {
            "turnover_year_1_inr_cr": 480.0,
            "turnover_year_2_inr_cr": 410.0,
            "turnover_year_3_inr_cr": 365.0,
            "best_year_inr_cr": 480.0,
        },
        "Form-5A": {
            "projects": [
                {"name": "Vishakhapatnam Outer Harbour Breakwater", "value_inr_cr": 195.0, "client": "Visakhapatnam Port Authority", "completion_date": "2023-12-10"},
                {"name": "Gangavaram Port Coal Berth", "value_inr_cr": 142.0, "client": "Gangavaram Port Ltd.", "completion_date": "2022-08-25"},
            ],
        },
        "Form-5C": {
            "breakwater_rmt": 850.0,
            "dredging_cum": 295000.0,
            "piling": [{"diameter_mm": 1000, "length_rmt": 320.0}],
        },
        "Form-6A": {
            # The defect is here: max_annual_value (45 Cr) is way below what's needed
            "max_annual_value_inr_cr": 45.0,
            "lookback_years": 10,
            "ongoing_commitments_inr_cr": 280.0,
            "contract_duration_years": DEMO_CONTRACT_DURATION_YEARS,
            "net_worth_inr_cr": 580.0,
            "solvency_inr_cr": 150.0,
            "solvency_cert_date": (BID_DATE - timedelta(days=110)).isoformat(),
        },
        "Form-2": _form2("C. Visweswara Rao"),
        "Form-12": {"signed": True, "signatory_name": "C. Visweswara Rao", "no_deviations": True, "no_intermediaries": True},
        "Form-13": {"signed": True, "signatory_name": "C. Visweswara Rao"},
        "Form-14": {
            "jv_entity_name": "Navayuga Engineering Company Ltd.",
            "partners": [{"name": "Navayuga Engineering Company Ltd.", "share_pct": 100.0, "lead": True}],
            "joint_and_several": True,
        },
        "Form-19": _form19_checklist(
            items_present=[
                "Form-1", "Form-2", "Form-3", "Form-4", "Form-5A", "Form-5C", "Form-6A",
                "Form-12", "Form-13", "Form-14", "Form-19", "Form-B Bid Bond",
                "EPF Cert", "ESI Cert", "PAN", "GST", "Solvency Cert",
                "Audited Financials Y1", "Audited Financials Y2", "Audited Financials Y3",
            ],
            items_missing=[],
        ),
        "Form-B": _bid_bond(payee="Navayuga Engineering Company Ltd."),
        "Bills": {"bill_1_inr_cr": 95.0, "bill_2_inr_cr": 110.0, "bill_3_inr_cr": 78.0, "bill_4_inr_cr": 52.0, "bill_5_inr_cr": 45.0, "grand_summary_inr_cr": 380.0},
    },
}


# ---- BID 05 — Stale Solvency + Bill Mismatch ----------------------------

BID_05_STALE_AND_BILL_MISMATCH: dict[str, Any] = {
    "vendor_name": "Hindustan Construction Company (HCC)",
    "jv_partners": ["Hindustan Construction Company Ltd."],
    "bid_value_inr_cr": 384.3,
    "submitted_at_iso": BID_DATE.isoformat(),
    "label": {
        "verdict": "Not Qualified",
        "expected_findings": ["FR-VAL-1.4", "FR-VAL-1.9"],
        "narrative": "Solvency certificate is 9 months old (max 6); Bills sum to 365 Cr but Grand Summary claims 380 Cr (₹15 Cr / 4% gap).",
    },
    "extractions": {
        "Form-3": {
            "company_name": "Hindustan Construction Company Ltd.",
            "registration_no": "L45200MH1926PLC001228",
            "address": "Hincon House, Mumbai, Maharashtra",
            "pan": "AAACH1234D",
            "gst": "27AAACH1234D1ZP",
        },
        "Form-4": {
            "turnover_year_1_inr_cr": 4520.0,
            "turnover_year_2_inr_cr": 3980.0,
            "turnover_year_3_inr_cr": 4210.0,
            "best_year_inr_cr": 4520.0,
        },
        "Form-5A": {
            "projects": [
                {"name": "Mumbai Trans Harbour Link Marine Section", "value_inr_cr": 612.0, "client": "MMRDA", "completion_date": "2024-04-30"},
                {"name": "Karaikal Port Berth Extension", "value_inr_cr": 198.0, "client": "Karaikal Port Pvt Ltd", "completion_date": "2022-11-08"},
            ],
        },
        "Form-5C": {
            "breakwater_rmt": 980.0,
            "dredging_cum": 380000.0,
            "piling": [{"diameter_mm": 1200, "length_rmt": 450.0}],
        },
        "Form-6A": {
            "max_annual_value_inr_cr": 612.0,
            "lookback_years": 10,
            "ongoing_commitments_inr_cr": 980.0,
            "contract_duration_years": DEMO_CONTRACT_DURATION_YEARS,
            "net_worth_inr_cr": 3400.0,
            "solvency_inr_cr": 450.0,
            # Defect 1: solvency certificate is 9 months old (max allowed: 6)
            "solvency_cert_date": (BID_DATE - timedelta(days=275)).isoformat(),
        },
        "Form-2": _form2("Arjun Dhawan"),
        "Form-12": {"signed": True, "signatory_name": "Arjun Dhawan", "no_deviations": True, "no_intermediaries": True},
        "Form-13": {"signed": True, "signatory_name": "Arjun Dhawan"},
        "Form-14": {
            "jv_entity_name": "Hindustan Construction Company Ltd.",
            "partners": [{"name": "Hindustan Construction Company Ltd.", "share_pct": 100.0, "lead": True}],
            "joint_and_several": True,
        },
        "Form-19": _form19_checklist(
            items_present=[
                "Form-1", "Form-2", "Form-3", "Form-4", "Form-5A", "Form-5C", "Form-6A",
                "Form-12", "Form-13", "Form-14", "Form-19", "Form-B Bid Bond",
                "EPF Cert", "ESI Cert", "PAN", "GST", "Solvency Cert",
                "Audited Financials Y1", "Audited Financials Y2", "Audited Financials Y3",
            ],
            items_missing=[],
        ),
        "Form-B": _bid_bond(payee="Hindustan Construction Company Ltd."),
        # Defect 2: bills sum to 365 but grand summary claims 380 (4% gap, > 0.1% tolerance)
        "Bills": {"bill_1_inr_cr": 92.0, "bill_2_inr_cr": 105.0, "bill_3_inr_cr": 73.0, "bill_4_inr_cr": 50.0, "bill_5_inr_cr": 45.0, "grand_summary_inr_cr": 380.0},
    },
}


# ---- BID 06 — Cross-bid collusion signal --------------------------------
# Same project listed by another bidder + identical bid value to bid 1 →
# triggers Layer-3 cross-bid anomaly detection.

BID_06_COLLUSION_SIGNAL: dict[str, Any] = {
    "vendor_name": "Patel-IRCON Marine JV",
    "jv_partners": ["Patel Engineering Ltd.", "IRCON International Ltd."],
    "bid_value_inr_cr": DEMO_BID_VALUE_CR,  # identical to others — first signal
    "submitted_at_iso": BID_DATE.isoformat(),
    "label": {
        "verdict": "Qualified",  # passes mandatory checks but raises anomaly flags
        "expected_findings": [],
        "narrative": "Mandatory checks pass, but cross-bid anomaly: same Dhamra Port project as Megha (different price/dates) — possible cartel signal.",
        "expected_anomalies": ["similar_experience_claim"],
    },
    "extractions": {
        "Form-3": {
            "company_name": "Patel-IRCON Marine JV",
            "registration_no": "JV-2025-PATEL-IRCON",
            "address": "c/o Patel Engineering Ltd., Mumbai",
            "pan": "AABCP9012E",
            "gst": "27AABCP9012E1ZN",
        },
        "Form-4": {
            "turnover_year_1_inr_cr": 4180.0,
            "turnover_year_2_inr_cr": 3850.0,
            "turnover_year_3_inr_cr": 3520.0,
            "best_year_inr_cr": 4180.0,
        },
        "Form-5A": {
            "projects": [
                # Almost-identical claim to Megha's Dhamra Port project
                {"name": "Dhamra Port Breakwater Extension", "value_inr_cr": 410.0, "client": "Dhamra Port Co. Ltd.", "completion_date": "2024-08-31"},
                {"name": "Mumbai Port Trust Container Berth", "value_inr_cr": 280.0, "client": "Mumbai Port Trust", "completion_date": "2023-04-12"},
            ],
        },
        "Form-5C": {
            "breakwater_rmt": 1180.0,
            "dredging_cum": 420000.0,
            "piling": [{"diameter_mm": 1200, "length_rmt": 480.0}],
        },
        "Form-6A": {
            "max_annual_value_inr_cr": 410.0,
            "lookback_years": 10,
            "ongoing_commitments_inr_cr": 350.0,
            "contract_duration_years": DEMO_CONTRACT_DURATION_YEARS,
            "net_worth_inr_cr": 1840.0,
            "solvency_inr_cr": 350.0,
            "solvency_cert_date": (BID_DATE - timedelta(days=80)).isoformat(),
        },
        "Form-2": _form2("Rupen Patel"),
        "Form-12": {"signed": True, "signatory_name": "Rupen Patel", "no_deviations": True, "no_intermediaries": True},
        "Form-13": {"signed": True, "signatory_name": "Rupen Patel"},
        "Form-14": {
            "jv_entity_name": "Patel-IRCON Marine JV",
            "partners": [
                {"name": "Patel Engineering Ltd.", "share_pct": 55.0, "lead": True, "role": "Lead — Marine breakwater works", "signed": True},
                {"name": "IRCON International Ltd.", "share_pct": 45.0, "lead": False, "role": "Onshore civil and approach roads", "signed": True},
            ],
            "joint_and_several": True,
            "all_partners_signed": True,
            "valid_through_dlp": True,
        },
        "Form-19": _form19_checklist(
            items_present=[
                "Form-1", "Form-2", "Form-3", "Form-4", "Form-5A", "Form-5C", "Form-6A",
                "Form-12", "Form-13", "Form-14", "Form-15", "Form-19", "Form-B Bid Bond",
                "EPF Cert", "ESI Cert", "PAN", "GST", "Solvency Cert",
                "Audited Financials Y1", "Audited Financials Y2", "Audited Financials Y3",
            ],
            items_missing=[],
        ),
        "Form-B": _bid_bond(payee="Patel-IRCON Marine JV"),
        "Bills": {"bill_1_inr_cr": 95.0, "bill_2_inr_cr": 110.0, "bill_3_inr_cr": 78.0, "bill_4_inr_cr": 52.0, "bill_5_inr_cr": 45.0, "grand_summary_inr_cr": 380.0},
    },
}


ALL_SYNTHETIC_BIDS = [
    BID_01_CLEAN,
    BID_02_MISSING_BG,
    BID_03_BG_NAME_MISMATCH,
    BID_04_CAPACITY_SHORTFALL,
    BID_05_STALE_AND_BILL_MISMATCH,
    BID_06_COLLUSION_SIGNAL,
]


def seed_synthetic_bids(db: Session, tender_id: int) -> int:
    """Idempotent: deletes any existing bids for tender, then loads the 5 synthetic ones."""
    db.query(Bid).filter(Bid.tender_id == tender_id).delete()
    db.commit()

    count = 0
    for spec in ALL_SYNTHETIC_BIDS:
        b = Bid(
            tender_id=tender_id,
            vendor_name=spec["vendor_name"],
            jv_partners=spec["jv_partners"],
            bid_value_inr=spec["bid_value_inr_cr"],
            submitted_at=datetime.fromisoformat(spec["submitted_at_iso"]),
            notes=json.dumps(spec["label"]),
        )
        db.add(b)
        db.flush()
        for form_no, payload in spec["extractions"].items():
            db.add(FormExtraction(
                bid_id=b.id,
                form_no=form_no,
                payload=payload,
                confidence=0.99,
            ))
        count += 1

    db.commit()
    return count
