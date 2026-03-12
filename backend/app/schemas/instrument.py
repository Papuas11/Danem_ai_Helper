from datetime import datetime

from pydantic import BaseModel, Field


class AliasCreate(BaseModel):
    alias: str


class AliasRead(BaseModel):
    id: int
    alias: str
    normalized_alias: str
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceCreate(BaseModel):
    service_type: str
    unit_type: str = "per_item"
    base_price: float
    base_cost: float
    turnaround_days: int | None = None
    turnaround_hours: int | None = None
    onsite_available: bool = False
    onsite_price: float | None = None
    onsite_cost: float | None = None
    required_client_data: list[str] = Field(default_factory=list)
    issued_documents: list[str] = Field(default_factory=list)
    status: str = "active"
    service_comment: str | None = None


class ServiceUpdate(ServiceCreate):
    pass


class ServiceRead(ServiceCreate):
    id: int
    instrument_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InstrumentCreate(BaseModel):
    name: str
    category: str
    status: str = "active"
    manager_comment: str | None = None


class InstrumentUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    status: str | None = None
    manager_comment: str | None = None


class InstrumentRead(InstrumentCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    aliases: list[AliasRead] = Field(default_factory=list)
    services: list[ServiceRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
