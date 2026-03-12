from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled deal")
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    manager_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    deal_probability: Mapped[float] = mapped_column(Float, nullable=False, default=5)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    parsed_instrument_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_service_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parsed_onsite: Mapped[str | None] = mapped_column(String(32), nullable=True)
    parsed_urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    missing_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculated_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    calculated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    calculated_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    calculated_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deviation_reason_tag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deviation_reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    events: Mapped[list["DealEvent"]] = relationship("DealEvent", back_populates="deal", cascade="all, delete-orphan")
    snapshots: Mapped[list["DealSnapshot"]] = relationship("DealSnapshot", back_populates="deal", cascade="all, delete-orphan")


class DealEvent(Base):
    __tablename__ = "deal_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    deal: Mapped[Deal] = relationship("Deal", back_populates="events")


class DealSnapshot(Base):
    __tablename__ = "deal_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    calculated_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    calculated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    calculated_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    deal_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    missing_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    deal: Mapped[Deal] = relationship("Deal", back_populates="snapshots")
