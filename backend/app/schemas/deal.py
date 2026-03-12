from datetime import datetime

from pydantic import BaseModel, Field


class DealAnalyzeRequest(BaseModel):
    input_text: str
    title: str = "Новая сделка"
    client_name: str | None = None


class DealRecalculateRequest(BaseModel):
    parsed_quantity: int | None = None
    parsed_onsite: str | None = None
    manager_notes: str | None = None
    final_price: float | None = None
    final_cost: float | None = None
    deviation_reason_tag: str | None = None
    deviation_reason_text: str | None = None


class DealCreate(DealAnalyzeRequest):
    pass


class DealUpdate(DealRecalculateRequest):
    input_text: str | None = None
    status: str | None = None


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
    missing_fields: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    draft_reply: str | None
    ai_used: bool = False
    ai_fallback_used: bool = False
    ai_missing_data_suggestions: list[str] = Field(default_factory=list)
    probability_explanation: str | None = None
    similar_deals_summary: str | None = None
    estimate_review: dict = Field(default_factory=dict)
    final_deviation_analysis: dict | None = None
    calculated_price: float | None
    calculated_cost: float | None
    calculated_profit: float | None
    calculated_margin: float | None
    final_price: float | None
    final_cost: float | None
    final_profit: float | None
    price_confirmed: bool
    deviation_reason_tag: str | None
    deviation_reason_text: str | None
    warnings: list[str] = Field(default_factory=list)
    similar_deals: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


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
    calculated_price: float | None
    calculated_cost: float | None
    calculated_profit: float | None
    deal_probability: float | None
    completeness_score: float | None
    missing_fields: str | None
    next_steps: str | None
    created_at: datetime

    class Config:
        from_attributes = True
