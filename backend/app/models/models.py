from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(255), default="general")
    status: Mapped[str] = mapped_column(String(50), default="active")
    manager_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    aliases = relationship("InstrumentAlias", back_populates="instrument", cascade="all, delete-orphan")
    services = relationship("InstrumentService", back_populates="instrument", cascade="all, delete-orphan")


class InstrumentAlias(Base):
    __tablename__ = "instrument_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(String(255), index=True)
    normalized_alias: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    instrument = relationship("Instrument", back_populates="aliases")


class InstrumentService(Base):
    __tablename__ = "instrument_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="CASCADE"))
    service_type: Mapped[str] = mapped_column(String(255))
    unit_type: Mapped[str] = mapped_column(String(50), default="per_item")
    base_price: Mapped[float] = mapped_column(Float, default=0.0)
    base_cost: Mapped[float] = mapped_column(Float, default=0.0)
    turnaround_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    turnaround_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    onsite_available: Mapped[bool] = mapped_column(Boolean, default=False)
    onsite_price: Mapped[float] = mapped_column(Float, default=0.0)
    onsite_cost: Mapped[float] = mapped_column(Float, default=0.0)
    required_client_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_documents: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    service_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instrument = relationship("Instrument", back_populates="services")


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="Untitled Deal")
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_text: Mapped[str] = mapped_column(Text, default="")
    manager_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    deal_probability: Mapped[float] = mapped_column(Float, default=5.0)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    parsed_instrument_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_service_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parsed_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parsed_onsite: Mapped[str | None] = mapped_column(String(20), nullable=True)
    parsed_urgency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    missing_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculated_price: Mapped[float] = mapped_column(Float, default=0.0)
    calculated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    calculated_profit: Mapped[float] = mapped_column(Float, default=0.0)
    calculated_margin: Mapped[float] = mapped_column(Float, default=0.0)
    final_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    deviation_reason_tag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deviation_reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("DealEvent", back_populates="deal", cascade="all, delete-orphan")
    snapshots = relationship("DealSnapshot", back_populates="deal", cascade="all, delete-orphan")


class DealEvent(Base):
    __tablename__ = "deal_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(100))
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deal = relationship("Deal", back_populates="events")


class DealSnapshot(Base):
    __tablename__ = "deal_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(100), default="analysis")
    calculated_price: Mapped[float] = mapped_column(Float, default=0.0)
    calculated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    calculated_profit: Mapped[float] = mapped_column(Float, default=0.0)
    deal_probability: Mapped[float] = mapped_column(Float, default=5.0)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    missing_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deal = relationship("Deal", back_populates="snapshots")
