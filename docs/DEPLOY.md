# AP-BidIQ — Deployment Guide

Deploy the demo to a **live URL** in ~30 minutes using:

- **Web (Next.js)** → Vercel (free tier)
- **API (FastAPI)** → Railway (free $5 credit / month)
- **Database (Postgres)** → Neon (free tier — serverless Postgres)

You'll need accounts on all three (free signup for each). Total monthly cost for the demo: **₹0**.

---

## Prerequisites

```bash
# Install CLIs
npm i -g vercel
brew install railway   # or: npm i -g @railway/cli

# Verify
vercel --version
railway --version
```

You'll also need a **GitHub account** if you want CI-style auto-deploy (recommended) — otherwise CLI deploy from local works too.

---

## Step 1 — Push the repo to GitHub

```bash
cd ~/Desktop/Desktop/Xprojects/AP-BidIQ
git add -A
git commit -m "Initial AP-BidIQ build"
gh repo create ap-bidiq --public --source=. --push    # uses GitHub CLI
```

If `gh` isn't installed: create the repo manually at github.com → then:
```bash
git remote add origin https://github.com/<your-user>/ap-bidiq.git
git branch -M main
git push -u origin main
```

---

## Step 2 — Create the Postgres database (Neon)

1. Sign in at <https://neon.tech>
2. Create a new project: **ap-bidiq** (region: Mumbai or Singapore for low latency to AP)
3. Copy the connection string (looks like `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`)
4. **Important**: convert the URL prefix from `postgresql://` to `postgresql+psycopg://` for SQLAlchemy + psycopg3:

```
postgresql+psycopg://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
```

Save this — you'll paste it as `DATABASE_URL` in Railway in step 3.

---

## Step 3 — Deploy the API (Railway)

```bash
cd api
railway login          # browser login, one-time
railway init           # create a project; pick "ap-bidiq-api"
railway up             # builds Dockerfile + deploys
```

Then in Railway's dashboard for this service → **Variables** → add:

| Key | Value |
|---|---|
| `DATABASE_URL` | (the Neon URL from step 2, with `+psycopg` prefix) |
| `ANTHROPIC_API_KEY` | (from console.anthropic.com — keep private) |
| `ANTHROPIC_MODEL_STRONG` | `claude-sonnet-4-6` |
| `ANTHROPIC_MODEL_FAST` | `claude-haiku-4-5` |
| `AUTO_SEED` | `1` (auto-loads corpus + bids on first boot) |
| `CORS_ORIGINS` | `["http://localhost:3000", "https://YOUR-VERCEL-URL.vercel.app"]` (set after step 4) |

Railway will assign a public URL like `https://ap-bidiq-api-production.up.railway.app`. Save it for step 4.

Smoke-test:
```bash
curl https://YOUR-RAILWAY-URL/health
# → {"status":"ok"}

curl https://YOUR-RAILWAY-URL/tenders
# → [{"id":1,"title":"EPCC Fishing Harbours Phase II",...}]
```

If `/tenders` returns `[]`, the auto-seed didn't fire — manually trigger:
```bash
railway run python -m app.cli ingest
railway run python -m app.cli seed-bids
railway run python -m app.cli validate-all  # populate validations + audit log
```

---

## Step 4 — Deploy the Web (Vercel)

```bash
cd ../web
vercel login
vercel link            # creates a project; pick "ap-bidiq"
vercel env add NEXT_PUBLIC_API_URL production
# When prompted, paste:  https://YOUR-RAILWAY-URL
vercel --prod
```

Vercel will assign a URL like `https://ap-bidiq.vercel.app`. Open it — you should see the tender list.

**Now go back to Railway** → update `CORS_ORIGINS` with your final Vercel URL and redeploy.

---

## Step 5 — Verify the deploy

Open your Vercel URL and click through:

1. ✅ Home — tender card visible
2. ✅ Click tender → corrigendum diff visible
3. ✅ Bids → 5 vendors, "Re-evaluate all bids" works
4. ✅ Click any bid → scorecard + citation drawer
5. ✅ Compare → matrix renders
6. ✅ Benchmark → 100% / 100% / 0
7. ✅ Audit → "✓ Chain verified · N entries"

If any step fails, check:
- Railway logs: `railway logs` or in the dashboard
- Vercel logs: `vercel logs <URL>` or in the dashboard
- Browser DevTools network tab for CORS errors

---

## Step 6 — Custom domain (optional, ~10 min)

In Vercel dashboard → Settings → Domains → add e.g. `bidiq.example.com`. Vercel walks you through DNS setup. Free SSL.

---

## Cost cap

To make sure the demo doesn't accidentally run up an Anthropic bill:

```bash
# In Anthropic console → Usage limits → set monthly cap
# Default $5 cap is plenty for the hackathon (each bid eval ≈ $0.005)
```

Each `/bids/{id}/validate` call uses ~3 Claude Sonnet 4.6 calls × ~600 input tokens × ~150 output tokens ≈ ₹2 per bid. Five bids × 50 evals = under ₹500.

---

## Tear-down (post-demo)

```bash
vercel remove ap-bidiq
railway down
# Neon: delete project from dashboard
```

---

## Troubleshooting

**`/tenders` returns empty after deploy**
- The `AUTO_SEED=1` env var must be set before first boot. If you set it later, run `railway run python -m app.cli ingest` and `seed-bids` once.

**LLM finds always fail with "LLM check failed"**
- `ANTHROPIC_API_KEY` not set or wrong. Check Railway variables.
- The L2 layer falls back to deterministic stubs if no key — verify under bid scorecard, "model_version" should be `llm-claude-sonnet-4-6`.

**CORS error in browser console**
- Add your Vercel URL to `CORS_ORIGINS` in Railway. Wildcard `*.vercel.app` is allowed by default.

**`pg_trgm extension not found` (Neon)**
- Not used in v1. Ignore. (Reserved for the future cross-bid anomaly detector.)

**Cold start lag (Railway free tier)**
- First request after idle takes ~5s. Not a real-demo concern (the demo flow keeps it warm).
