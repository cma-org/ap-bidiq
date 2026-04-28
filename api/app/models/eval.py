from datetime import datetime
from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EvalStatement(Base):
    __tablename__ = "eval_statements"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id", ondelete="CASCADE"))
    verdict: Mapped[str] = mapped_column(String(32))     # qualified | not_qualified | conditional
    reasons: Mapped[list[dict]] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    docx_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    json_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
