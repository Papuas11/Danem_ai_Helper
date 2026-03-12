from datetime import datetime
from pydantic import BaseModel


class AliasCreate(BaseModel):
    alias: str


class AliasRead(BaseModel):
    id: int
    instrument_id: int
    alias: str
    normalized_alias: str
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceCreate(BaseModel):
    service_type: str
    unit_type: str = "per_item"
    base_price: float = 0.0
    base_cost: float = 0.0
    turnaround_days: int | None = None
    turnaround_hours: int | None = None
    onsite_available: bool = False
    onsite_price: float = 0.0
    onsite_cost: float = 0.0
    required_client_data: str | None = None
    issued_documents: str | None = None
    status: str = "active"
    service_comment: str | None = None


class ServiceRead(ServiceCreate):
    id: int
    instrument_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InstrumentCreate(BaseModel):
    name: str
    category: str = "general"
    status: str = "active"
    manager_comment: str | None = None


class InstrumentUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    status: str | None = None
    manager_comment: str | None = None


class InstrumentRead(BaseModel):
    id: int
    name: str
    category: str
    status: str
    manager_comment: str | None
    created_at: datetime
    updated_at: datetime
    aliases: list[AliasRead] = []
    services: list[ServiceRead] = []

    class Config:
        from_attributes = True
