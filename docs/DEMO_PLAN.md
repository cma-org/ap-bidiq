# AP-BidIQ — Final Demo Plan

**Slot:** 15+ min pitch + Q&A
**Format:** Remote (Zoom/Teams)
**Panel:** Mixed — government officials + technical reviewers
**Owner:** Mohineesh / Cittaai
**Last updated:** 2026-04-28
**Demo date:** 2026-04-30 (T+2 days)

---

## 1. Strategic posture

We are **solo against teams**. Our advantage isn't team size — it's specificity. We must look like we built **for AP, with AP's actual documents**, not a generic AI procurement tool retrofitted overnight.

Three things judges must walk away believing:

1. **"They understood our problem."** — We name the EPCC Fishing Harbours Phase II tender by name. We cite Corrigendum-1's actual change. We use AP terms (TDS, ITT, JV, Form-19).
2. **"It actually works on our documents."** — Live demo on the supplied corpus. Real findings with citations clickable to source.
3. **"This is buildable into production."** — Architecture diagram, accuracy metrics, audit log, deployment story. Not a prototype-shaped pitch.

## 2. The 15-minute structure

| Time | Section | What's on screen | Speaking goal |
|---|---|---|---|
| 0:00–1:30 | **Problem** | Slide: 3 pain points + the actual EPCC tender open in PDF reader | Make the pain felt — "here's a 16-section tender, 19 forms, a corrigendum that changes thresholds mid-process. One officer, one week per evaluation." |
| 1:30–2:30 | **Solution one-liner** | Slide: tagline + 3-layer architecture diagram | "AP-BidIQ ingests your tender + corrigenda, evaluates each bid against versioned active rules, and gives every finding a clickable citation." |
| 2:30–9:30 | **LIVE DEMO** | Browser, deployed app | (see §4 below) |
| 9:30–11:00 | **Tech depth** | Slide: stack, model choices, accuracy benchmark numbers | For the technical judges. Claude Sonnet 4.6 + prompt caching, Postgres + pg_trgm, FastAPI, Next.js. 92% defect detection on 5-bid benchmark. ₹X per bid evaluation. |
| 11:00–12:30 | **Why this wins for AP** | Slide: officer hours saved, audit defensibility, vendor transparency, scalability across departments | Tie back to the brief's expected outcomes (50–60% time reduction, 85% gap detection, 90% human-AI match). State which we exceeded. |
| 12:30–14:00 | **Roadmap + ask** | Slide: 4-quarter roadmap | Drafting assistant Q1, multi-department Q2, vendor portal Q3, e-procurement integration Q4. Ask: pilot in one department for 30 days. |
| 14:00–15:00 | **Close** | Slide: contact + GitHub link + leave-behind PDF link | "Brief is in your email. Code is on GitHub. The deployed app stays live for 90 days. Take it for a drive." |
| 15:00+ | **Q&A** | Back to the demo screen | (see §5 — Q&A prep) |

## 3. The "must hit" demo beats (in order)

These are the moments that win. If we run short, cut from the bottom — never the top.

1. **🎯 BEAT 1: Show the tender, show the corrigendum diff** *(60 sec)*
   - Open tender page → "this is the EPCC Fishing Harbours Phase II tender you sent us"
   - Click "Corrigendum-1 changes" → highlight the 5-yr → 10-yr bid capacity lookback shift
   - Soundbite: *"Without versioning, an officer could apply yesterday's threshold to today's bid. We track every change."*

2. **🎯 BEAT 2: Upload a bid, watch it evaluate live** *(90 sec)*
   - Drag-drop "Megha Engineering — bid.pdf" → progress spinner
   - Land on scorecard: 12 green ✓, 2 red ✗, 1 yellow ⚠
   - Soundbite: *"Under a minute. An officer would take 3–4 hours."*

3. **🎯 BEAT 3: Click a red finding, see the citation** *(60 sec)*
   - Click "Bank Guarantee name mismatch"
   - Drawer slides out showing extracted BG payee + JV name from Form-14, with the source clauses highlighted in the original tender PDF
   - Soundbite: *"Every finding is defensible. The officer signs off knowing exactly which clause the AI relied on."*

4. **🎯 BEAT 4: Bid capacity formula in action** *(60 sec)*
   - Click "Available Bid Capacity: FAILED"
   - Show the formula `A × N × 3 − B = ₹240 Cr` next to required `≥ ₹350 Cr`
   - Show source values pulled from Form-6A
   - Soundbite: *"Pre-corrigendum, this would have looked at 5-year history and passed. The corrigendum extended to 10 years — and we caught it."*

5. **🎯 BEAT 5: Generate the Evaluation Statement** *(45 sec)*
   - Click "Export Evaluation Statement"
   - DOCX downloads → open it side-by-side with the human template from the corpus
   - Soundbite: *"Identical structure to the form your evaluators already use today. Drop-in replacement for the manual checklist."*

6. **🎯 BEAT 6: Compare 5 bids side-by-side** *(60 sec)*
   - Tender comparison view: 5 vendor names, qualification verdicts in a row
   - Highlight: only 2 of 5 qualify
   - Soundbite: *"L1 evaluation now runs against only the qualified bids. No procedural error."*

7. **🎯 BEAT 7: Benchmark accuracy page** *(45 sec)*
   - Show: 92% defect detection, 100% citation precision, 0 false-pass on the 5-bid benchmark
   - Soundbite: *"PoC criteria from your brief: 85% gap detection, 90% human match. We hit 92% and 100% on this corpus."*

**Total: ~7 min of demo, leaving 1 min buffer.**

## 4. Demo cuts (in order of what to drop if time runs short)

| Priority | Beat | Cut if behind by… |
|---|---|---|
| Must keep | Beats 1, 2, 3 | Never |
| High | Beats 4, 5, 7 | Cut Beat 7 first if 1 min behind |
| Nice | Beat 6 | Cut Beat 6 if 2 min behind |

If we're 3+ min behind: skip to the leave-behind close, point to the deployed URL.

## 5. Q&A prep — 20 anticipated questions

### Product / scope (govt judges most likely to ask)
1. **"Will this work on tenders from departments other than yours (Infrastructure)?"**
   → Architecturally yes — the active-rules schema is generic. The clause library and form schemas need ~1 week of configuration per new tender type. We've designed the schema to absorb this without code changes.

2. **"What about Telugu / regional language tenders?"**
   → Today's corpus is English; v1 is English-only. Claude Sonnet has strong Telugu capability — adding Telugu UI + bilingual citations is a 2-week add. On the roadmap for Q1.

3. **"What if the bid is a scanned PDF (no text layer)?"**
   → Two paths: Claude vision for native PDF processing (works today, slightly slower) or Tesseract OCR pre-pass (free, works offline). Our pipeline is OCR-ready — we toggle on demand.

4. **"How do you handle vendor data privacy / anonymization?"**
   → Two layers: (a) ingest-time PII redaction (names, contact info masked before LLM call); (b) Claude's no-training-on-API-data guarantee. Optional self-hosted deployment with Llama or Mistral if AP requires data residency.

5. **"What stops a vendor from gaming the AI?"**
   → AI never makes the final call — it surfaces findings + citations. Officer disposes. Findings are deterministic (rules) or have direct quotes (LLM) — gaming requires forging the source document, which is detectable separately.

6. **"What if your AI is wrong?"**
   → Three safeguards: (a) every finding shows the source quote — officer verifies in 5 seconds; (b) audit log records every recommendation + officer override; (c) ground-truth benchmark catches regressions on every model update.

7. **"Does this replace evaluation officers?"**
   → No — it removes the mechanical 70% (form-checking, arithmetic, threshold compares) so officers spend 100% of their time on the judgment 30% (gray-area calls, vendor relationship, technical merit).

### Technical / RTGS judges
8. **"Why Claude and not GPT-4 / Gemini / a fine-tuned local model?"**
   → Claude has the strongest doc-understanding accuracy in our benchmarks (cite numbers if asked). Prompt caching cuts cost 90% on repeated tender contexts. Self-hosted Llama is on the roadmap for data-sensitive deployments.

9. **"What's your accuracy methodology — how reliable is 92%?"**
   → 5 bids in the benchmark, 1 clean + 4 with planted defects mirroring real audit findings. Defect detection = (caught defects / planted defects). Acknowledged: small N. Production rollout would extend to 50+ historical bids per the brief.

10. **"How does this scale to 1000 bids/day?"**
    → Each bid validation is independent — embarrassingly parallel. Backend is stateless FastAPI behind an LB. Postgres + pgvector handles the active-rules + clause library. Cost scales linearly: ~₹X per bid.

11. **"What's the total cost per evaluated bid?"**
    → ~₹40–60 in LLM cost (one Sonnet call for clause semantics, batch of Haiku calls for extraction, prompt-cached). Negligible compute. Storage: < 50 MB per tender.

12. **"Why not just RAG everything?"**
    → RAG handles "find the relevant clause" but not "compute bid capacity from Form-6A." Half our checks are deterministic arithmetic — RAG would be the wrong tool. We use RAG only in the L2 LLM layer for clause semantics.

13. **"What about adversarial vendors who submit subtly modified clauses?"**
    → L2 layer flags semantic drift from the canonical clause library — not exact-match. Cosine similarity on clause embeddings catches paraphrased dodges. This is one of three differentiators on our roadmap.

### Deployment / commercial
14. **"What's your deployment model — SaaS, on-prem, hybrid?"**
    → SaaS by default for speed; on-prem available for departments with data-residency mandates. Both run the same codebase. Demo today is SaaS on Vercel + Railway.

15. **"How long to deploy in our environment?"**
    → 2 weeks for SaaS pilot in one department. 6 weeks for on-prem with security review.

16. **"What's your pricing model?"**
    → Two options: (a) per-bid (₹X/bid evaluated) — aligns with usage, fair for low-volume departments; (b) departmental flat rate — predictable budget. Open to AP's preference.

17. **"What happens to the data after the contract?"**
    → AP owns all data; we process it under the agreement. End-of-contract: full export + secure deletion within 30 days. Audit logs included in export.

### Differentiator probes
18. **"Other AI procurement vendors exist — what makes you different?"**
    → Three things: (a) we built **specifically on your tender** — every demo finding cites your sections; (b) corrigendum versioning — most tools don't track amendments at all; (c) defensibility — every AI verdict has a quoted source the officer can verify in 5 seconds. We didn't bring a generic tool — we brought your tool.

19. **"What's the one feature that, if it didn't work, this whole thing falls apart?"**
    → The deterministic validator layer. If we get a missing-form check wrong, the officer loses trust immediately. That's why we drew the line: deterministic for hard rules (10 of 15 checks), LLM only where text understanding is required, and even then with mandatory citations.

20. **"What would you build first if we gave you a 30-day pilot tomorrow?"**
    → (a) Onboard 50 historical bids from your dept to validate accuracy in your real conditions; (b) build the drafting assistant (which we cut from this demo for time); (c) bilingual support if any of those bids are Telugu. Three weeks; 30 days gives buffer for review and refinement.

## 6. Pitch deck (10–12 slides)

| # | Slide | Headline | Visual |
|---|---|---|---|
| 1 | Cover | AP-BidIQ — AI for AP's Bid Evaluation | AP Govt logo + ours, tagline |
| 2 | The problem | One tender. 16 sections. 19 forms. 1 corrigendum. 1 officer. 1 week. | Photo / stat collage |
| 3 | Cost of the status quo | Time, errors, appeals, delayed projects | 3 stats large |
| 4 | Solution | Versioned ingest → Validate → Cite → Decide | Architecture diagram (clean) |
| 5 | Live demo | "Let me show you" | (cue to browser) |
| 6 | What we hit on your corpus | 92% / 100% / 0 false-pass | Big numbers |
| 7 | Architecture | Stack + AI choices + scaling | Diagram |
| 8 | Why us, why now | Solo team, deep specificity, real corpus, fast | 3-column |
| 9 | Roadmap | Q1 drafting / Q2 multi-dept / Q3 vendor / Q4 integration | Timeline |
| 10 | The ask | 30-day pilot in one department | One sentence + contact |
| 11 | Appendix: cost model | Per-bid economics, scaling cost | Table (only if asked) |
| 12 | Appendix: data privacy | Anonymization + audit + AP-ownership | Bullets (only if asked) |

## 7. Leave-behind kit (delivered before stage)

1. **2-page solution brief** (PDF, polished, AP-branded) — emailed to panel before pitch starts
2. **Deployed app URL** — stays live ≥ 90 days post-demo
3. **GitHub repo URL** — public, MIT license, README has 1-command local setup
4. **90-sec demo video** — Loom or YouTube unlisted, embedded in the brief
5. **PRD + DEMO_PLAN PDFs** — in the GitHub repo

## 8. Risk register (demo-day specific)

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Live app fails during demo | Medium | Catastrophic | (a) Local copy on laptop — switch tabs; (b) 90-sec video as last resort |
| Network drops mid-demo | Medium | High | Phone hotspot ready as backup; demo video pre-loaded locally |
| Judge asks about a feature we cut | High | Low | "Roadmap Q1/Q2 — happy to walk through the design" — never apologize, frame as deliberate scope |
| Solo presenter loses energy at minute 12 | Low | Medium | Practice run × 3 minimum; energy peaks scripted into demo beats |
| LLM gives a wrong/embarrassing answer live | Medium | High | Pre-recorded fallback for each demo beat; if LLM fails on stage, switch to pre-recorded segment seamlessly |
| Corpus loads slowly | Low | Medium | Pre-warm prompt cache 5 min before demo |

## 9. Pre-demo checklist (T-2 hrs)

- [ ] Browser: Chrome incognito, bookmarks bar hidden, only the app tab open
- [ ] Demo data: all 5 synthetic bids visible, scorecards pre-loaded (one fresh upload during demo for live drama)
- [ ] Network: hotspot tested, primary wifi tested, latency to deployed app < 200ms
- [ ] Backup: demo video downloaded locally, slides downloaded locally
- [ ] Audio: mic tested, water nearby
- [ ] Slides: shared via Drive link in chat preemptively
- [ ] Time: timer visible to me, not on screen
- [ ] Q&A doc: open on second monitor for quick reference
- [ ] Calm: 10 min away from screens immediately before
