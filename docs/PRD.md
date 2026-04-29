# AP-BidIQ — Product Requirements Document (v1, Hackathon Demo)

**Owner:** Mohineesh / Cittaai
**Last updated:** 2026-04-28
**Status:** Locked for 2-day demo build
**Hackathon:** AI-Based Bid Document Drafting and Evaluation Automation — AP Govt. Infrastructure & Investment Department
**Demo deadline:** 2026-04-30 (T+2 days from 2026-04-28)

---

## 1. Problem

Public procurement in Andhra Pradesh runs on long, structured tender packages (the EPCC Fishing Harbours Phase II tender we received is 16 sections, ~1 MB of text, 19 vendor forms). Today:

- **Drafting** RFPs is manual copy-paste from prior tenders. Project-specific thresholds and corrigenda are easy to miss.
- **Validation** of submitted bids is a checklist exercise done by hand. Mandatory annexures are missed, BG (Bank Guarantee) names don't match the JV name, bill totals don't reconcile, and stale solvency certificates slip through.
- **Evaluation** at qualification stage is binary (pass/fail) but spread across ~15 mandatory items + computable thresholds (turnover, bid capacity formula, specialized-work quantities). Errors here trigger rejections, appeals, and project delays.
- **Corrigenda** mid-tender (e.g., the live Corrigendum-1 in our corpus changed bid-capacity lookback 5→10 yrs) are tracked manually and inconsistently applied.

A procurement officer evaluating 5 bids spends ~2–3 days per tender on validation alone. Subjectivity and inconsistency cost both speed and trust.

## 2. Opportunity

A focused AI tool that ingests an RFP package + corrigenda → versions the active rules → ingests vendor bids → produces a **deterministic compliance scorecard with cited sources** that mirrors the human Evaluation Statement format. Officer reviews and approves; AI never auto-rejects.

This directly hits the hackathon brief's PoC success criteria:
- ≥85% accuracy on missing-clause / compliance-gap detection
- ≥90% match between AI verdict and human expert verdict

## 3. Goals (v1, 2-day scope)

**G1.** Ingest the supplied EPCC Fishing Harbours Phase II tender package + Corrigendum-1 → produce a versioned, machine-readable "active rules" object (thresholds, mandatory clauses, qualification criteria).

**G2.** Ingest a vendor bid (DOCX/PDF) → extract structured data for the 8 highest-value forms (Form-3, 4, 5A, 5B, 5C, 6A, 14, 19).

**G3.** Run a three-layer validator (deterministic rules → LLM clause semantics → cross-bid anomaly) and produce a per-bid compliance scorecard with **citations to source clauses**.

**G4.** Generate an Evaluation Statement output that mirrors the human evaluator template in the corpus.

**G5.** Demonstrate ≥85% defect detection on a benchmark set of 5 synthetic bids (1 clean + 4 with planted defects).

**G6.** Ship a live, deployed web app the panel can click through.

## 4. Non-Goals (explicit cuts for v1)

- **Drafting assistant.** Brief asks for it; v1 does evaluation only. Demo will mention drafting as a roadmap module, not a built feature.
- **Multi-department / multi-tender-type generalization.** v1 is scoped to **one tender type** (EPCC Fishing Harbour) using **the supplied corpus only**.
- **Real e-procurement integration.** No live API to AP's e-procurement portal. Mocked.
- **Telugu / bilingual UI.** Corpus is English-only; English-only UI for v1.
- **Auth / RBAC.** Single-officer demo; no login screen. Mention as roadmap.
- **Real OCR for scanned PDFs.** v2: shipped Tesseract + poppler pipeline with English + Telugu language packs. Toggle in upload UI.
- **Drafting assistant clause-suggestion RAG.** Not in v1.
- **Production audit/security hardening.** Audit log is implemented (it's a brief requirement) but not pen-tested.

## 5. Users & Personas

**Primary user — Procurement Officer (Department / RTGS):**
- Reviews 3–10 bids per tender at qualification stage.
- Wants: fast, defensible verdicts with traceable sources.
- Pain: manual checklist work, hard-to-defend subjective calls, missed corrigenda.

**Secondary user — Department Head (read-only):**
- Wants dashboards and audit confidence; not in v1 UI but mentioned in pitch.

**Stakeholder — Vendor (not a user of v1):**
- Benefits indirectly from consistent, transparent evaluation.

## 6. Demo target & success criteria

| # | Criterion | Target | How measured |
|---|---|---|---|
| S1 | End-to-end demo runs live on deployed URL | Yes | Judge clicks → working app |
| S2 | Versioned RFP rules generated from corpus + Corrigendum-1 | Yes | UI shows pre/post-corrigendum diff for bid-capacity lookback |
| S3 | Vendor bid ingest produces structured JSON | 8 forms | Inspector view in UI |
| S4 | Defect detection accuracy on synthetic benchmark | ≥85% | Benchmark report page in app |
| S5 | Every finding has a clickable citation | 100% | Every red/green item links to source clause text |
| S6 | Evaluation Statement output matches human template structure | Side-by-side OK | Compare to corpus's Evaluation Statements doc |
| S7 | Audit log is append-only and tamper-evident | Hash-chained | Show audit log view with hash per row |

## 7. Functional requirements

### 7.1 RFP Ingest (FR-RFP)
- **FR-RFP-1**: System accepts a folder of RFP section files (DOCX/DOC/PDF) and one or more corrigendum files.
- **FR-RFP-2**: System parses each section into a structured `Tender` object: `{tender_id, title, department, sections[], thresholds[], mandatory_clauses[], forms_required[], qualification_criteria[]}`.
- **FR-RFP-3**: System parses each corrigendum into a list of `Patch` operations (clause replace, threshold update, deadline extension).
- **FR-RFP-4**: System produces a versioned `ActiveRules` view: original + N corrigenda applied = current effective rules. Each rule carries its source provenance (section + clause + which corrigendum, if any, modified it).
- **FR-RFP-5**: UI shows a diff view: "What changed because of Corrigendum-1?"

### 7.2 Vendor Bid Ingest (FR-BID)
- **FR-BID-1**: System accepts a vendor bid as a single DOCX or PDF (or a folder).
- **FR-BID-2**: For each of the 8 priority forms (3, 4, 5A, 5B, 5C, 6A, 14, 19), system extracts a typed JSON record per the form's schema.
- **FR-BID-3**: System computes derived fields: 3-year average turnover, total similar-work value, available bid capacity (`A × N × 3 − B`), JV partners list, signed-form list.
- **FR-BID-4**: System stores raw bid + extracted JSON + extraction confidence per field.

### 7.3 Validator (FR-VAL)
**Layer 1 — Deterministic checks (must implement all 10):**
- **FR-VAL-1.1**: All mandatory forms present (Form-19 checklist completeness).
- **FR-VAL-1.2**: EMD/Bid Bond present, amount ≥ TDS-specified threshold, validity ≥ 180 days from bid submission date.
- **FR-VAL-1.3**: BG issuer's named bidder matches Form-14 JV entity name (string match + fuzzy).
- **FR-VAL-1.4**: Solvency certificate dated within 6 months of bid date.
- **FR-VAL-1.5**: Bid capacity: `A × N × 3 − B ≥ Bid Value`.
- **FR-VAL-1.6**: Annual turnover (best of last 7 years) ≥ TDS threshold.
- **FR-VAL-1.7**: Similar-work value (best of last 5 years) ≥ TDS threshold.
- **FR-VAL-1.8**: Specialized work thresholds (breakwater Rmt, dredging Cum, piling diameter & Rmt) all met.
- **FR-VAL-1.9**: Bill summation: Σ(Bills 1–5) = Grand Summary total (tolerance ≤ 0.1%).
- **FR-VAL-1.10**: Performance Security validity covers contract end date + DLP + 90 days.

**Layer 2 — LLM clause semantics (OpenAI GPT-4o, must cite source, PII redacted):**
- **FR-VAL-2.1**: Integrity Pact present and signed by authorized signatory listed in Form-2 PoA.
- **FR-VAL-2.2**: JV agreement contains explicit "joint and several liability" language.
- **FR-VAL-2.3**: Power of Attorney scope covers bid signing + contract execution.
- **FR-VAL-2.4**: Form-12 declarations: no deviations, no intermediaries, no exceptions.
- **FR-VAL-2.5**: Each finding returns a citation `{section, clause, page_or_offset, quoted_text}`.

**Layer 3 — Cross-bid anomalies (run when ≥2 bids loaded):**
- **FR-VAL-3.1**: Fuzzy-match experience claims (project name + client + value + dates) across all bids; flag ≥80% similarity.
- **FR-VAL-3.2**: Subcontractor name overlap across bids.
- **FR-VAL-3.3**: Methodology language similarity (embedding cosine ≥ 0.92).

### 7.4 Evaluation Statement (FR-EVAL)
- **FR-EVAL-1**: Generate a per-bid statement matching the column structure of the human "Evaluation Statements Updated.docx" in the corpus (criteria | required | submitted | meets/doesn't | remarks).
- **FR-EVAL-2**: Roll up to a single qualification verdict: **Qualified / Not Qualified**, with reason list.
- **FR-EVAL-3**: Export as DOCX (matches human format) and JSON.

### 7.5 Officer Dashboard (FR-UI)
- **FR-UI-1**: Tender list page → click a tender → see active rules + corrigendum diff.
- **FR-UI-2**: Bid upload page (drag-drop DOCX/PDF).
- **FR-UI-3**: Bid detail page: scorecard with red/yellow/green per check, citation drawer that opens to show source clause.
- **FR-UI-4**: Tender comparison page: all bids side-by-side with cross-bid anomaly flags.
- **FR-UI-5**: Audit log page: append-only, hash-chained, every AI finding + (placeholder) officer action.

### 7.6 Audit Log (FR-AUD)
- **FR-AUD-1**: Every validator finding writes one row: `{ts, tender_id, bid_id, check_id, verdict, evidence_ref, model_version, prev_hash, this_hash}`.
- **FR-AUD-2**: `this_hash = SHA256(prev_hash || row_payload)`.
- **FR-AUD-3**: UI shows a "verify chain" button.

## 8. Non-functional requirements

| | Requirement | Target |
|---|---|---|
| NFR-1 | Time to validate one bid (end-to-end) | < 60 s |
| NFR-2 | Concurrent bids in benchmark run | ≥ 5 |
| NFR-3 | LLM cost per bid validation | < ₹50 (~$0.60) — use prompt caching on RFP context |
| NFR-4 | Citation precision (citation actually points to relevant text) | ≥ 90% on benchmark |
| NFR-5 | Deployment: live URL | Vercel + Railway + Neon |
| NFR-6 | Source code license | MIT in repo |

## 9. System architecture

```
┌──────────────────────────┐         ┌──────────────────────────┐
│  Next.js (Vercel)        │  HTTPS  │  FastAPI (Railway)       │
│  • Officer dashboard     │ ──────► │  • /tenders, /bids,      │
│  • Upload UI             │         │    /validate, /eval      │
│  • Citation drawer       │         │  • Claude API client     │
│  • Audit log viewer      │         │  • Validator layers      │
└──────────────────────────┘         └────────────┬─────────────┘
                                                   │
                                                   ▼
                                       ┌──────────────────────┐
                                       │  Postgres (Neon)     │
                                       │  + pg_trgm for fuzzy │
                                       │    matching          │
                                       └──────────────────────┘
                                                   │
                                                   ▼
                                       ┌──────────────────────┐
                                       │  Object storage      │
                                       │  (Railway volume or  │
                                       │   S3) for raw docs   │
                                       └──────────────────────┘

External: Anthropic Claude API (Sonnet 4.6 for validation, Haiku 4.5 for batch
extraction). Prompt caching on RFP context — single 200K-token cache hit
serves all bids for that tender.
```

## 10. Data model (Postgres)

```sql
tenders          (id, title, department, created_at)
sections         (id, tender_id, name, raw_text, source_path)
corrigenda       (id, tender_id, name, raw_text, applied_at)
patches          (id, corrigendum_id, target_clause, op, before, after)
active_rules     (id, tender_id, version, json_blob, generated_at)
forms_required   (id, tender_id, form_no, title, schema_json)
mandatory_clauses(id, tender_id, code, title, source_section, source_text)

bids             (id, tender_id, vendor_name, jv_partners[], submitted_at, raw_path)
form_extractions (id, bid_id, form_no, json_payload, confidence, raw_excerpt)

validations      (id, bid_id, check_id, layer, verdict, severity, message,
                  citation_section, citation_clause, citation_text, model_version)

cross_bid_flags  (id, tender_id, bid_a, bid_b, flag_type, similarity, evidence)

eval_statements  (id, bid_id, verdict, reasons_json, docx_path, json_path)

audit_log        (id, ts, actor, action, payload_json, prev_hash, this_hash)
```

## 11. Demo dataset

**Real corpus (in `data/corpus/`):**
- EPCC Fishing Harbours Phase II — 13 sections (Sections 1-10, 6A/B/C)
- Top-level RFP for PMC services
- Evaluation Statements Updated.docx (human evaluator template — our ground truth)
- Corrigendum-1.docx (live amendment to demo versioning)

**Synthetic vendor bids (`data/synthetic-bids/`):**
1. **`bid-01-clean.docx`** — fully compliant, should pass.
2. **`bid-02-missing-bg.docx`** — Form-19 ticked but BG annexure absent. Tests FR-VAL-1.1 + 1.2.
3. **`bid-03-bg-name-mismatch.docx`** — BG issued to lead JV partner, not the JV entity. Tests FR-VAL-1.3.
4. **`bid-04-capacity-shortfall.docx`** — bid capacity computed as `A × N × 3 − B` falls below bid value. Tests FR-VAL-1.5 + arithmetic.
5. **`bid-05-stale-solvency-and-bill-mismatch.docx`** — solvency cert 9 months old + Bills don't sum to Grand Summary. Tests FR-VAL-1.4 + 1.9. Plus copies methodology language verbatim from bid-01 to trigger FR-VAL-3.3.

**Ground-truth labels** in `data/synthetic-bids/labels.json`:
```json
{
  "bid-01-clean": { "verdict": "Qualified", "expected_findings": [] },
  "bid-02-missing-bg": { "verdict": "Not Qualified", "expected_findings": ["FR-VAL-1.1", "FR-VAL-1.2"] },
  ...
}
```

Accuracy = (correct verdicts + correct findings) / total expected.

## 12. UI flows

```
/                           → Tender list (1 tender pre-loaded)
/tenders/:id                → Active rules view + corrigendum diff
/tenders/:id/bids           → Bid list (5 synthetic bids pre-loaded)
/tenders/:id/bids/upload    → Drag-drop new bid
/bids/:id                   → Scorecard (3 layers, citations)
/bids/:id/eval-statement    → Generated Evaluation Statement (DOCX preview)
/tenders/:id/compare        → Cross-bid anomaly view
/audit                      → Audit log with hash-chain verifier
/benchmark                  → Accuracy report on synthetic set (for the panel)
```

## 13. Out of scope (roadmap to mention on stage)

- Drafting assistant (RAG over clause library)
- Multi-tender-type templates (works, services, goods, consultancy)
- Telugu UI + bilingual clause search
- Real e-procurement portal integration
- Vendor portal (today's UI is officer-side only)
- Auth / RBAC / SSO with department IdP
- OCR for scanned PDFs
- Tender drafting assistant
- Mobile-responsive UI
- Real anonymization pipeline at ingest

## 14. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Claude API key not ready in time | Scaffold + run extractor against text-extracted corpus; switch to API once key arrives |
| 2-day timeline slips | Drop FR-VAL-3 (cross-bid) first, then FR-AUD hash chain, then UI polish — never the deterministic validator |
| Deploy fails day-of | Local-laptop fallback ready; record screen video as last-resort backup |
| Synthetic bids feel toy-ish to judges | Frame on stage: "we used your real RFP and engineered defects mirroring patterns in past tender appeals" |
| Judge asks "what about scanned PDFs?" | Roadmap answer; mention Claude vision + Tesseract fallback |
| LLM gives wrong citation | Citation is rendered with quoted text; officer sees the quote and can verify in one glance |

## 15. Open questions

1. Do we have a domain SME (retired procurement officer / consultant) we can show this to before stage? Strongly recommended for sanity-check.
2. Is presentation on AP-provided hardware or our laptop? Affects deploy vs. local fallback priority.
3. Are we expected to leave the codebase with AP afterward? If yes, add a 1-page handoff doc to docs/.
4. Any AP branding constraints (colors, logo) to bake into UI?

---

## Appendix A — Mandatory check matrix (all 15 from corpus, marked v1 vs roadmap)

| # | Check | Source | v1 layer |
|---|---|---|---|
| 1 | EMD present + valid + correct amount | ITT 1.12, Form-B | L1 |
| 2 | Tender Document Integrity (Form-12) | Form-12 | L2 |
| 3 | Company Registration | ITT 1.6.2(a) | L1 |
| 4 | EPF/ESI Registration | ITT 1.6.2(b) | L1 |
| 5 | PAN & GST Registration | ITT 1.6.2(c) | L1 |
| 6 | Power of Attorney (notarized, ≤6mo) | Form-2 | L1 + L2 |
| 7 | Audited financial statements (3 yrs) | Form-4, QR 3.1 | L1 |
| 8 | Experience certificates (gov: EE+SE; pvt: TDS+CA) | Form-5A/B/C, QR 4.1 | L2 |
| 9 | Equipment list | Form-8 | L1 (presence only) |
| 10 | Key personnel + CVs | Form-9 | L1 (presence only) |
| 11 | Integrity Pact signed | Form-13 | L2 |
| 12 | JV Agreement (joint & several) | Form-14 | L2 |
| 13 | PoA for Lead JV Member | Form-15 | L2 |
| 14 | No-exceptions declaration | Form-12 | L2 |
| 15 | Bid Form + Price Schedule arithmetic | Section 4 + 10 | L1 |

## Appendix B — Bid capacity formula

Per ITT 1.6.1 (as amended by Corrigendum-1):

```
Available Bid Capacity = (A × N × 3) − B

A = max annual contract value executed in any year of the last 10 years
    (was 5 years pre-corrigendum)
N = duration of current contract in years
B = value of existing commitments and ongoing works to be completed in
    next N years
```

Pass condition: `Available Bid Capacity ≥ Submitted Bid Value`.
