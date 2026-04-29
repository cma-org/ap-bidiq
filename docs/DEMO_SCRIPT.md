# AP-BidIQ — Demo Script (15-min slot)

**Read aloud, beat by beat. Time targets in [brackets].**
**Live URLs:** Web: https://ap-bidiq.vercel.app · API: https://ap-bidiq-api-production.up.railway.app
**Backup:** localhost demo + 90-sec recorded video

---

## OPENING [0:00–1:30] — The problem

> "Good [morning/afternoon]. I'm Mohineesh from Cittaai.
>
> The Infrastructure Department sent us **one tender** to build against — the EPCC Fishing Harbours Phase II package. We received **sixteen documents totalling roughly one megabyte of structured legal text**. **Nineteen vendor forms** to verify per bid. **Fifteen mandatory clauses**. And a **corrigendum** that quietly amended the bid-capacity lookback period from five years to ten — silently disqualifying any bidder relying on years six through ten of historical capacity.
>
> Today, an officer evaluating five such bids spends **two to three days each**, manually. Errors trigger appeals. Delays compound. And the officer carries the audit risk personally.
>
> We built a system that does this in under sixty seconds, with every decision defensible to citation."

---

## SOLUTION OVERVIEW [1:30–2:30]

*(Show slide 4 — architecture diagram)*

> "The system has three pieces:
>
> One — we **ingest your tender plus corrigenda** and produce a versioned ActiveRules object. Every threshold, every clause, with provenance.
>
> Two — we run a **three-layer validator** on every vendor bid. Layer one is deterministic: arithmetic, formula compute, threshold compares. Layer two is LLM-driven, using OpenAI GPT-4o, for clause-semantics that need text understanding. Layer three is cross-bid anomaly detection — collusion patterns. Every finding cites a quoted source.
>
> Three — we generate an **Evaluation Statement** that mirrors the format your evaluators already use. Drop-in replacement for the manual checklist.
>
> Critically: **the AI never auto-rejects**. It surfaces; the officer disposes."

---

## LIVE DEMO [2:30–9:30]

*(Switch to browser at https://ap-bidiq.vercel.app)*

### Beat 1 — The tender + corrigendum diff [2:30–3:30]

*(On the home page)*

> "This is the tender list — currently ingested: **EPCC Fishing Harbours Phase II**, your real package. You can see one corrigendum has been applied."

*(Click the tender card → tender detail page)*

> "The active rules are versioned. **Version one** is the baseline; **version two** has Corrigendum-1 applied. Look at this diff —"

*(Scroll to Corrigendum Diff section)*

> "ITT 1.6.1, Available Bid Capacity. Before: 'last Five years.' After: 'last Ten years.' Without versioning, an officer could apply yesterday's threshold to today's bid. **We track every change.**
>
> And here — the extras-items protocol your corrigendum formalised. Ten percent threshold, monthly statement before the fifteenth, Committee approval. Captured."

### Beat 2 — Bid list, all 5 evaluated [3:30–4:30]

*(Click "View Bids →")*

> "Five vendors have submitted: Megha, L&T, Afcons-Tata JV, Navayuga, HCC — all real Indian infra contractors. The system has already evaluated each.
>
> Only **Megha qualifies**. Four bids fail. Let me show you why one fails — pick the most interesting."

*(Click Navayuga Engineering Company Ltd.)*

### Beat 3 — Bid scorecard with citations [4:30–6:00]

> "Navayuga. Bid value: ₹380 crore. **Not Qualified.** Twelve checks pass, one fails.
>
> The disqualification reason is right there at the top: **Available Bid Capacity is less than Bid Value.**
>
> Now watch this —"

*(Click the failing finding to open citation drawer)*

> "Every finding has a clickable citation. The math is shown: A times N times three, minus B. Forty-five crore times three years times three, minus two-eighty crore in existing commitments — **equals one twenty-five crore. Which is below the bid value of three-eighty crore. Disqualified.**
>
> And the source — Section 1, ITT 1.6.1, **'as amended by Corrigendum-1'**. The officer reads the source quote, sees the math, signs off. **Five seconds.**"

*(Close drawer. Scroll down to other findings)*

> "Notice the L1 versus L2 badges. L1 is deterministic — pure rules and arithmetic, no LLM ambiguity. L2 is the Claude Sonnet layer — clause semantics like Integrity Pact authorised-signatory match, JV joint-and-several liability. These also cite their source."

### Beat 4 — Evaluation Statement export [6:00–6:45]

*(Scroll to Evaluation Statement section)*

> "And here's what the officer signs and files. Same six-column format your evaluators use today: criterion, required, submitted, meets, remarks, with the citation underneath. Drop-in."

*(Click Export DOCX button)*

> "One click — proper Word document, AP-branded. This goes straight into the file."

### Beat 5 — Comparison view [6:45–7:30]

*(Top nav → Compare)*

> "Five vendors, ten checks, one matrix. Pattern detection at a glance. L&T failed on missing forms and EMD. Afcons-Tata on the BG name mismatch. Navayuga on capacity. HCC on stale solvency and bill summation.
>
> **Only Megha proceeds to the L1 financial round.**"

### Beat 6 — Benchmark [7:30–8:15]

*(Top nav → Benchmark)*

> "Your brief specified two PoC criteria: eighty-five percent gap detection, ninety percent human-AI verdict match.
>
> On this corpus, with five bids — one clean baseline, four with planted defects mirroring real audit findings —
>
> **One hundred percent defect detection. One hundred percent verdict match. Zero false positives.**"

### Beat 7 — Audit log [8:15–9:00]

*(Top nav → Audit)*

> "And every AI recommendation is logged in a tamper-evident chain. SHA-256 hash linking each row to the previous. **'Chain verified.'** If anyone modifies a row after the fact, the chain breaks and we surface it. CAG-friendly."

### *(Optional: re-evaluate live for drama)* [9:00–9:30]

*(Back to bids list, click "Re-evaluate all bids")*

> "And to prove this is live — re-evaluating all five right now. Three Claude calls per bid, prompt-cached on the shared tender context. **Under sixty seconds end-to-end.**"

---

## TECH DEPTH [9:30–11:00]

*(Slide 7 — architecture stack)*

> "For the engineers in the room: Next.js 16, React 19 frontend on Vercel. FastAPI with SQLAlchemy on Railway. Postgres on Neon — Singapore region for AP latency.
>
> OpenAI GPT-4o for clause semantics + drafting; GPT-4o-mini for batch extraction. **Prompt caching cuts cost by ninety percent** on the shared tender context — each bid evaluation costs about two rupees. Provider-flexible architecture — switching to Claude or self-hosted Llama is a single-file change.
>
> Audit log: SHA-256 hash chain in Postgres, verifiable in one SQL query. Sub-sixty-second latency per bid. Embarrassingly parallel — scales linearly to thousands of bids per day."

---

## WHY US [11:00–12:30]

*(Slide 8)*

> "Three differentiators.
>
> One — **we built on your actual tender**. Every demo finding cites your real sections by number. Not a generic AI procurement tool retrofitted overnight.
>
> Two — **corrigendum versioning**. Most procurement tools ignore amendments entirely. We diff them, version them, apply them automatically.
>
> Three — **defensibility**. Every AI verdict carries a quoted source the officer can verify in five seconds. The audit log makes the entire decision trail tamper-evident. The officer has never been more comfortable signing off."

---

## ROADMAP + ASK [12:30–14:30]

*(Slide 9 — roadmap)*

> "Q1: Drafting Assistant — RAG over your clause library.
> Q2: Multi-department generalisation.
> Q3: Vendor portal plus e-procurement portal API.
> Q4: Cross-bid anomaly detection — collusion and cartelisation patterns.
>
> *(Slide 10)*
>
> What we'd ask: **a thirty-day pilot in the Infrastructure Department**. We onboard fifty historical bids, validate accuracy in your real conditions, add the drafting assistant. Telugu support if you need it. Your data stays in your AWS region. Cost to AP for the pilot — **zero**. We absorb compute and labour.
>
> If we hit production-quality numbers on those fifty bids, we discuss a longer engagement. If we don't, you walk away."

---

## CLOSE [14:30–15:00]

*(Slide 11 — contact)*

> "The deployed app stays live for ninety days at **ap-bidiq.vercel.app**. The source code is on GitHub at **cma-org/ap-bidiq** — public, MIT license. Two-page brief is in your inbox.
>
> **Take it for a drive. Then call us.**
>
> Happy to take questions."

---

## Q&A — Cheat sheet (open DEMO_PLAN.pdf §5 on second monitor)

20 anticipated questions. Top 5 they'll most likely ask:

1. **"Will this work on tenders from other departments?"** → Schema is generic. ~1 week clause library config per new tender type. No code changes.
2. **"Telugu / regional language?"** → Q1 roadmap. Claude has strong Telugu. ~2 weeks to add.
3. **"What if AI is wrong?"** → Source quote shown for every finding (officer verifies in 5s); audit log; benchmark catches regressions.
4. **"Privacy / data residency?"** → Anonymisation at ingest; Claude no-train guarantee; self-hosted Llama option for residency mandates.
5. **"Pricing?"** → ₹2/bid in compute, plus your engagement fee. Per-bid OR departmental flat — your preference.

---

## Pre-demo checklist (T-30 min)

- [ ] **Wake the API** — visit https://ap-bidiq-api-production.up.railway.app/health (Railway free tier sleeps after idle)
- [ ] **Wake the web** — visit https://ap-bidiq.vercel.app and click through Tenders → Bids → bid 4
- [ ] **Pre-warm prompt cache** — click "Re-evaluate all bids" once so subsequent eval is faster on stage
- [ ] **Browser** — Chrome incognito, only the app tab open, bookmarks bar hidden
- [ ] **Hotspot** — phone tethered, tested
- [ ] **Backup video** — downloaded locally, ready in second tab
- [ ] **Slides** — DEMO_PLAN.pdf open on second monitor for Q&A
- [ ] **Mic + camera** — tested
- [ ] **Water** — within reach
- [ ] **Mind** — 10 min away from screens immediately before
