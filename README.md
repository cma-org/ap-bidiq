# AP-BidIQ

**AI for Andhra Pradesh's Public Procurement** — ingest tender documents and corrigenda, evaluate vendor bids against versioned active rules, and produce defensible compliance scorecards with clickable citations.

Built for the AP Govt. Hackathon (Infrastructure & Investment Department): *AI-Based Bid Document Drafting and Evaluation Automation*.

## What it does

1. **Ingest** an RFP package (16+ sections) + any corrigenda → produce a versioned, machine-readable `ActiveRules` object (thresholds, mandatory clauses, qualification criteria, forms required).
2. **Extract** structured data from a vendor bid (DOCX/PDF) for the priority forms (Form-3, 4, 5A/B/C, 6A, 14, 19).
3. **Validate** the bid through three layers — deterministic rules, LLM clause semantics with citations, and cross-bid anomaly detection.
4. **Generate** an Evaluation Statement that mirrors the human evaluator's template.

## Repo layout

```
.
├── web/                  Next.js 15 (App Router) — officer dashboard
├── api/                  FastAPI — ingest, extract, validate, eval
├── data/
│   ├── corpus/           Real EPCC Fishing Harbours Phase II tender + Corrigendum-1 + Eval Statements
│   └── synthetic-bids/   5 synthetic vendor bids (1 clean + 4 with planted defects)
└── docs/
    ├── PRD.md/.pdf       Product requirements (locked v1 scope)
    └── DEMO_PLAN.md/.pdf 15-min final-demo strategy
```

## Stack

- **Frontend**: Next.js 15, TypeScript, Tailwind, shadcn/ui
- **Backend**: FastAPI (Python 3.12), SQLAlchemy, Alembic
- **Database**: Postgres (Neon for prod, local Postgres for dev) + `pg_trgm`
- **AI**: Anthropic Claude — Sonnet 4.6 for clause-semantics validation, Haiku 4.5 for batch extraction. Prompt caching on tender context.
- **Deploy**: Vercel (web) + Railway (api) + Neon (db)

## Local development

```bash
make setup        # install web + api deps
make dev          # run web (3000) + api (8000) + local postgres
make seed         # ingest the EPCC corpus + load synthetic bids
make benchmark    # run the accuracy benchmark on synthetic bids
```

See [docs/PRD.md](docs/PRD.md) for full requirements, [docs/DEMO_PLAN.md](docs/DEMO_PLAN.md) for the demo strategy.

## License

MIT
