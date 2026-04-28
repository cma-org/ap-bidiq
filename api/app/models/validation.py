from datetime import datetime
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Validation(Base):
    __tablename__ = "validations"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id", ondelete="CASCADE"))
    check_id: Mapped[str] = mapped_column(String(64))     # e.g., "FR-VAL-1.3"
    layer: Mapped[str] = mapped_column(String(8))          # L1 | L2 | L3
    verdict: Mapped[str] = mapped_column(String(16))       # pass | fail | warning
    severity: Mapped[str] = mapped_column(String(16))      # info | minor | major | critical
    title: Mapped[str] = mapped_column(String(256))
    message: Mapped[str] = mapped_column(Text)
    citation_section: Mapped[str | None] = mapped_column(String(256), nullable=True)
    citation_clause: Mapped[str | None] = mapped_column(String(64), nullable=True)
    citation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CrossBidFlag(Base):
    __tablename__ = "cross_bid_flags"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    bid_a: Mapped[int] = mapped_column(ForeignKey("bids.id", ondelete="CASCADE"))
    bid_b: Mapped[int] = mapped_column(ForeignKey("bids.id", ondelete="CASCADE"))
    flag_type: Mapped[str] = mapped_column(String(64))  # similar_experience | shared_subcontractor | language_overlap
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
