import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models import Tender
from app.routers import tenders, bids, validations, eval as eval_router, benchmark, audit, draft, anomalies, upload, admin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup. Prod would use Alembic migrations.
    Base.metadata.create_all(bind=engine)

    # Auto-seed corpus + bids if the DB is empty (so a fresh deploy is demo-ready).
    if os.environ.get("AUTO_SEED", "0") in ("1", "true", "True"):
        db = SessionLocal()
        try:
            if db.query(Tender).count() == 0:
                from app.ingest.rfp import ingest_corpus
                from app.ingest.synthetic_bids import seed_synthetic_bids

                # Search a few likely locations for the corpus dir.
                candidates = [
                    Path(settings.corpus_dir),
                    Path(__file__).resolve().parent.parent.parent / "data" / "corpus",
                    Path("/app/data/corpus"),
                ]
                corpus_dir = next((p for p in candidates if p.exists()), None)
                if corpus_dir:
                    report = ingest_corpus(db, corpus_dir)
                    seed_synthetic_bids(db, report.tender_id)
        finally:
            db.close()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# CORS: allow localhost dev + any *.vercel.app subdomain; "*" only in dev.
allow_origin_regex = r"https://([a-z0-9-]+\.)*vercel\.app"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenders.router)
app.include_router(bids.router)
app.include_router(validations.router)
app.include_router(eval_router.router)
app.include_router(benchmark.router)
app.include_router(audit.router)
app.include_router(draft.router)
app.include_router(anomalies.router)
app.include_router(upload.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "environment": settings.environment,
        "status": "ok",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
