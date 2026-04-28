# AP-BidIQ — Pitch Deck

**Slot:** 15 min + Q&A · **Audience:** Mixed govt + technical · **Format:** Remote (Zoom/Teams)

---

## Slide 1 — Cover

# AP-BidIQ
## AI-Powered Bid Evaluation for AP Procurement

Submitted to: AP Hackathon — *AI for Governance and Procurement Efficiency*
Department: Infrastructure & Investment, Government of Andhra Pradesh

**Cittaai · 2026-04-30**

---

## Slide 2 — The Problem

> One tender. **16 sections. 19 forms. 1 corrigendum. 1 officer. 1 week.**

The EPCC Fishing Harbours Phase II package you sent us:
- 16 documents totalling **~1 MB of structured legal text**
- **19 vendor forms** to verify per bid
- **15 mandatory clauses** to check
- **Quantitative thresholds** scattered across TDS, ITT, QR, and a corrigendum
- **Corrigendum-1** silently changed the bid-capacity lookback from 5 to 10 years

Today an officer evaluates 5 bids per tender, manually, in **2-3 days each**.
Errors trigger appeals. Delays compound. Evaluators carry the audit risk.

---

## Slide 3 — The Cost of the Status Quo

| Pain | Impact |
|---|---|
| Manual checklist work | 70% of officer time on mechanical reconciliation |
| Inconsistent application of corrigenda | Disputed verdicts, appeals, re-tenders |
| Subjective evaluation | Vendor mistrust, RTI queries, judicial intervention |
| No audit trail of *why* a bid was rejected | Hard-to-defend decisions; officer personal risk |

---

## Slide 4 — Solution

# **Versioned Ingest → Layered Validation → Defensible Citation → Officer Decides**

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  RFP + Corr.    │ ──► │  ActiveRules v1, │ ──► │  Per-bid        │
│  ingested       │     │  v2 (post-corr.) │     │  scorecard      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                              ┌────────────────────────────┘
                              ▼
            ┌──────────────────────────────────────────┐
            │  L1 Deterministic (10 checks)            │
            │  → Bid capacity formula, EMD, JV name…   │
            ├──────────────────────────────────────────┤
            │  L2 LLM Clause-Semantics (Claude Sonnet) │
            │  → Integrity Pact, JV liability… cited.  │
            └──────────────────────────────────────────┘
                              │
                              ▼
            ┌──────────────────────────────────────────┐
            │  Evaluation Statement (matches AP form)  │
            │  + Hash-chained audit log                │
            └──────────────────────────────────────────┘
```

**AI never auto-rejects. Officer reviews every finding with a 1-click source citation.**

---

## Slide 5 — LIVE DEMO

> *Switch to browser — open the deployed app.*

**Demo flow** (~7 min, mirrors §3 of DEMO_PLAN):
1. Tender page → Corrigendum-1 diff (5→10 yr lookback)
2. Bid list → 5 vendors evaluated
3. Click bid → 13-check scorecard
4. Click finding → citation drawer (quoted source)
5. Bid capacity formula failure: `(45×3×3) − 280 = ₹125 Cr < ₹380 Cr`
6. Generated Evaluation Statement (matches AP human format)
7. Comparison view → 1 of 5 qualifies for L1
8. Audit log → "✓ Chain verified · 25 entries"

---

## Slide 6 — What We Hit on Your Corpus

# Brief targets — exceeded.

| Metric | Brief target | **AP-BidIQ** |
|---|---|---|
| Defect detection accuracy | ≥ 85% | **100.0%** |
| Verdict match with human | ≥ 90% | **100.0%** |
| False positive count | (lower better) | **0** |

Tested on **5 vendor bids** (1 clean baseline + 4 with planted defects mirroring real audit findings). 13 compliance checks per bid (10 deterministic + 3 LLM-driven).

> *Caveat surfaced proactively:* small N. Production rollout extends benchmarking to the 50+ historical bids per the brief.

---

## Slide 7 — Architecture

| Layer | Stack | Why |
|---|---|---|
| Frontend | Next.js 16 + Tailwind | Officer dashboard; sub-second navigation |
| API | FastAPI (Python 3.12) | Best ecosystem for doc parsing + LLM SDKs |
| Database | Postgres (Neon) + SQLite for dev | Transparent dev/prod parity via SQLAlchemy |
| AI | **Claude Sonnet 4.6** (clause semantics) + **Haiku 4.5** (batch extraction) | Strongest accuracy on Indian legal/procurement text; prompt caching cuts cost 90% on repeated tender context |
| Audit | SHA-256 hash chain in Postgres | Tamper-evident; verifies in 1 SQL query |
| Hosting | Vercel + Railway + Neon | All free tier for the demo; on-prem option available |

**Cost per bid evaluated: ~₹2** (3 LLM calls × cached context).
**Latency: < 60s end-to-end** for a fresh upload.

---

## Slide 8 — Why Us, Why Now

| Differentiator | Most generic AI procurement tools | **AP-BidIQ** |
|---|---|---|
| Built on AP's actual tender | ✗ — retrofit demos | ✓ — your EPCC + Corrigendum-1 |
| Corrigendum versioning | ✗ — ignored | ✓ — versioned ActiveRules with diff view |
| Officer-defensibility | ✗ — black-box scores | ✓ — every finding cites quoted source |
| Bid-capacity formula compute | ✗ — only NLP | ✓ — `A×N×3−B` deterministic, with corrigendum-aware A_lookback |
| Tamper-evident audit | ✗ — log files | ✓ — hash chain, in-app verifier |

**Bottom line:** *We didn't bring a generic tool. We brought your tool.*

---

## Slide 9 — Roadmap (post-pilot)

| Quarter | Module |
|---|---|
| **Q1** | Drafting Assistant — RAG over AP clause library + project-type templates |
| **Q2** | Multi-department generalisation — works, services, goods, consultancy |
| **Q3** | Vendor portal + e-procurement portal API integration |
| **Q4** | Cross-bid anomaly detection — collusion/cartelisation patterns |

Beyond Q4: Telugu UI · OCR for scanned bids · Mobile officer app · API for state CAG audit access.

---

## Slide 10 — The Ask

# **30-day pilot in the Infrastructure & Investment Department**

What we'd do:
- Onboard **50 historical bids** to validate accuracy in real conditions
- Add the **drafting assistant** (cut from this demo for time)
- Add **bilingual support** if any of those bids include Telugu content
- White-glove training for **2 procurement officers**
- All AP data stays in your AWS region; full export at end of pilot

**Cost to AP for the 30-day pilot: ₹0** (we absorb compute + labour).

---

## Slide 11 — Contact

**Mohineesh / Cittaai**
✉ tech@cittaai.com
🔗 GitHub: github.com/cma-org/ap-bidiq *(repo link)*
🌐 Live demo: ap-bidiq.vercel.app *(deployed URL)*

Leave-behind kit: 2-page brief + this deck + 90-sec demo video — all in your inbox.

---

# Appendix

## A — Cost economics
3 Sonnet calls × 600 input + 150 output tokens, 90% prompt-cache hit on shared RFP context = **₹2 / bid evaluated**. At 1,000 bids/month = ₹2,000.

## B — Privacy & data residency
- AP data never used for model training (Claude API contract).
- Optional self-hosted: Llama 3.1 70B on AP infrastructure (~3-week migration).
- PII redaction at ingest (vendor contact info masked before LLM call).

## C — Anticipated questions
*(See Q&A section of DEMO_PLAN.md — 20 questions pre-answered.)*
