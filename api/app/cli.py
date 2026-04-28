"""CLI for seeding, benchmarking, and admin tasks. Run via `python -m app.cli ...`."""
from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.ingest.rfp import ingest_corpus

app_cli = typer.Typer(help="AP-BidIQ admin CLI")


@app_cli.command()
def init_db():
    """Drop + recreate all tables (DEV ONLY)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rprint("[green]✓ tables recreated[/]")


@app_cli.command()
def ingest(
    corpus_dir: str | None = typer.Option(None, help="Path to corpus directory"),
):
    """Ingest the RFP corpus + corrigenda into the DB."""
    settings = get_settings()
    p = Path(corpus_dir or settings.corpus_dir).resolve()
    if not p.exists():
        rprint(f"[red]corpus dir not found: {p}[/]")
        raise typer.Exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        report = ingest_corpus(db, p)
        rprint(f"[green]✓ ingested tender_id={report.tender_id}[/]")
        rprint(f"  sections:           {report.sections_loaded}")
        rprint(f"  corrigenda:         {report.corrigenda_loaded}")
        rprint(f"  patches detected:   {report.patches_detected}")
        rprint(f"  active rule versions: {report.active_rule_versions}")
        if report.notes:
            rprint("[yellow]notes:[/]")
            for n in report.notes:
                rprint(f"  - {n}")
    finally:
        db.close()


@app_cli.command()
def seed_bids(tender_id: int = 1):
    """Load the 5 synthetic vendor bids into the DB."""
    from app.ingest.synthetic_bids import seed_synthetic_bids
    db = SessionLocal()
    try:
        n = seed_synthetic_bids(db, tender_id=tender_id)
        rprint(f"[green]✓ seeded {n} synthetic bids for tender_id={tender_id}[/]")
    finally:
        db.close()


@app_cli.command()
def validate_all(tender_id: int = 1):
    """Run deterministic validators against every bid for a tender."""
    from app.models import Bid
    from app.validators.deterministic import persist_findings, run_deterministic_validators
    db = SessionLocal()
    try:
        bids = db.query(Bid).filter(Bid.tender_id == tender_id).all()
        for b in bids:
            findings = run_deterministic_validators(db, b.id)
            persist_findings(db, b.id, findings)
            fails = [f for f in findings if f.verdict == "fail"]
            status = "[red]FAIL[/]" if fails else "[green]PASS[/]"
            rprint(f"{status} bid_id={b.id:>2}  {b.vendor_name:<55}  {len(findings) - len(fails)}✓ / {len(fails)}✗")
            for f in fails:
                rprint(f"        - {f.check_id} {f.title}")
    finally:
        db.close()


@app_cli.command()
def show_rules(tender_id: int = 1):
    """Print the latest ActiveRules JSON for a tender."""
    from app.models import ActiveRules
    db = SessionLocal()
    try:
        rows = db.query(ActiveRules).filter(ActiveRules.tender_id == tender_id).order_by(ActiveRules.version).all()
        for r in rows:
            rprint(f"\n[bold cyan]── ActiveRules v{r.version} ─────────[/]")
            rprint(r.payload)
    finally:
        db.close()


if __name__ == "__main__":
    app_cli()
