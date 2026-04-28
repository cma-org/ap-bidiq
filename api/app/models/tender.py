from datetime import datetime
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Tender(Base):
    __tablename__ = "tenders"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    department: Mapped[str] = mapped_column(String(256))
    code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sections: Mapped[list["Section"]] = relationship(back_populates="tender", cascade="all, delete-orphan")
    corrigenda: Mapped[list["Corrigendum"]] = relationship(back_populates="tender", cascade="all, delete-orphan")
    forms_required: Mapped[list["FormRequired"]] = relationship(back_populates="tender", cascade="all, delete-orphan")
    mandatory_clauses: Mapped[list["MandatoryClause"]] = relationship(back_populates="tender", cascade="all, delete-orphan")
    active_rules: Mapped[list["ActiveRules"]] = relationship(back_populates="tender", cascade="all, delete-orphan")


class Section(Base):
    __tablename__ = "sections"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(256))
    order_idx: Mapped[int] = mapped_column(Integer, default=0)
    raw_text: Mapped[str] = mapped_column(Text)
    source_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    tender: Mapped["Tender"] = relationship(back_populates="sections")


class Corrigendum(Base):
    __tablename__ = "corrigenda"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(256))
    order_idx: Mapped[int] = mapped_column(Integer, default=1)
    raw_text: Mapped[str] = mapped_column(Text)
    applied_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tender: Mapped["Tender"] = relationship(back_populates="corrigenda")
    patches: Mapped[list["Patch"]] = relationship(back_populates="corrigendum", cascade="all, delete-orphan")


class Patch(Base):
    __tablename__ = "patches"
    id: Mapped[int] = mapped_column(primary_key=True)
    corrigendum_id: Mapped[int] = mapped_column(ForeignKey("corrigenda.id", ondelete="CASCADE"))
    target_clause: Mapped[str] = mapped_column(String(256))  # e.g., "ITT 1.6.1"
    op: Mapped[str] = mapped_column(String(32))  # replace | append | delete | threshold_update
    before_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    semantic_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    corrigendum: Mapped["Corrigendum"] = relationship(back_populates="patches")


class ActiveRules(Base):
    """Versioned snapshot of effective rules after applying N corrigenda."""
    __tablename__ = "active_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tender: Mapped["Tender"] = relationship(back_populates="active_rules")


class FormRequired(Base):
    __tablename__ = "forms_required"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    form_no: Mapped[str] = mapped_column(String(32))  # e.g., "Form-19"
    title: Mapped[str] = mapped_column(String(256))
    schema: Mapped[dict] = mapped_column(JSON, default=dict)

    tender: Mapped["Tender"] = relationship(back_populates="forms_required")


class MandatoryClause(Base):
    __tablename__ = "mandatory_clauses"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(64))  # e.g., "MAND-EMD"
    title: Mapped[str] = mapped_column(String(256))
    source_section: Mapped[str] = mapped_column(String(256))
    source_text: Mapped[str] = mapped_column(Text)
    layer: Mapped[str] = mapped_column(String(8), default="L1")  # L1 | L2

    tender: Mapped["Tender"] = relationship(back_populates="mandatory_clauses")
