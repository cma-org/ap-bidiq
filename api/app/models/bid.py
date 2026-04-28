from datetime import datetime
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Bid(Base):
    __tablename__ = "bids"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    vendor_name: Mapped[str] = mapped_column(String(256))
    jv_partners: Mapped[list[str]] = mapped_column(JSON, default=list)
    bid_value_inr: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    raw_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    extractions: Mapped[list["FormExtraction"]] = relationship(back_populates="bid", cascade="all, delete-orphan")


class FormExtraction(Base):
    __tablename__ = "form_extractions"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id", ondelete="CASCADE"))
    form_no: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    raw_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    bid: Mapped["Bid"] = relationship(back_populates="extractions")
