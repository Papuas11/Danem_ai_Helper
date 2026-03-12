from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    manager_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    aliases: Mapped[list["InstrumentAlias"]] = relationship("InstrumentAlias", back_populates="instrument", cascade="all, delete-orphan")
    services: Mapped[list["InstrumentService"]] = relationship("InstrumentService", back_populates="instrument", cascade="all, delete-orphan")


class InstrumentAlias(Base):
    __tablename__ = "instrument_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    instrument: Mapped[Instrument] = relationship("Instrument", back_populates="aliases")


class InstrumentService(Base):
    __tablename__ = "instrument_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    service_type: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(64), nullable=False, default="per_item")
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    base_cost: Mapped[float] = mapped_column(Float, nullable=False)
    turnaround_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    turnaround_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    onsite_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onsite_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    onsite_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    required_client_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string list
    issued_documents: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    service_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    instrument: Mapped[Instrument] = relationship("Instrument", back_populates="services")
