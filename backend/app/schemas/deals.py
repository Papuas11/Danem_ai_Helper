from datetime import datetime
from pydantic import BaseModel


class DealCreate(BaseModel):
    title: str = "Untitled Deal"
    client_name: str | None = None
    input_text: str = ""
    manager_notes: str | None = None


class DealUpdate(BaseModel):
    title: str | None = None
    client_name: str | None = None
    input_text: str | None = None
    manager_notes: str | None = None
    parsed_quantity: int | None = None
    parsed_onsite: str | None = None
    final_price: float | None = None
    final_cost: float | None = None
    deviation_reason_tag: str | None = None
    deviation_reason_text: str | None = None


class DealRead(BaseModel):
    id: int
    title: str
    client_name: str | None
    input_text: str
    manager_notes: str | None
    status: str
    deal_probability: float
    completeness_score: float
    parsed_instrument_name: str | None
    parsed_service_type: str | None
    parsed_quantity: int | None
    parsed_onsite: str | None
    parsed_urgency: str | None
    ai_confidence: float
    missing_fields: str | None
    next_steps: str | None
    draft_reply: str | None
    calculated_price: float
    calculated_cost: float
    calculated_profit: float
    calculated_margin: float
    final_price: float | None
    final_cost: float | None
    final_profit: float | None
    price_confirmed: bool
    deviation_reason_tag: str | None
    deviation_reason_text: str | None
    warnings: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    input_text: str
    title: str = "Analyzed Deal"


class RecalculateRequest(BaseModel):
    parsed_quantity: int | None = None
    parsed_onsite: str | None = None
    manager_notes: str | None = None
    final_price: float | None = None
    final_cost: float | None = None
    deviation_reason_tag: str | None = None
    deviation_reason_text: str | None = None


class DealEventRead(BaseModel):
    id: int
    deal_id: int
    event_type: str
    field_name: str | None
    old_value: str | None
    new_value: str | None
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DealSnapshotRead(BaseModel):
    id: int
    deal_id: int
    source: str
    calculated_price: float
    calculated_cost: float
    calculated_profit: float
    deal_probability: float
    completeness_score: float
    missing_fields: str | None
    next_steps: str | None
    created_at: datetime

    class Config:
        from_attributes = True
