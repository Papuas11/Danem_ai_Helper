import json
from sqlalchemy.orm import Session
from app.models.models import Deal, DealEvent, DealSnapshot
from app.services.analysis import (
    calculate_economics,
    completeness,
    draft_reply,
    next_steps,
    parse_text,
    probability,
    similar_deals,
    warnings,
)


def run_analysis(db: Session, deal: Deal) -> Deal:
    parsed = parse_text(db, deal.input_text)
    comp = completeness(parsed, parsed.service)
    econ = calculate_economics(parsed.service, deal.parsed_quantity or parsed.quantity, deal.parsed_onsite or parsed.onsite)
    similar = similar_deals(db, parsed.instrument.name if parsed.instrument else None, parsed.service.service_type if parsed.service else None, limit=3)
    prob, prob_reason = probability(parsed, comp["score"], econ, len([d for d in similar if d.final_price and d.final_price > 0]))
    steps = next_steps(comp["missing"], deal.parsed_onsite or parsed.onsite, parsed.confidence)
    draft = draft_reply(comp["missing"], econ["price"])
    warns = warnings(parsed, econ, comp["missing"], deal.final_price)

    deal.parsed_instrument_name = parsed.instrument.name if parsed.instrument else None
    deal.parsed_service_type = parsed.service.service_type if parsed.service else None
    deal.parsed_quantity = deal.parsed_quantity or parsed.quantity
    deal.parsed_onsite = deal.parsed_onsite or parsed.onsite
    deal.parsed_urgency = parsed.urgency
    deal.ai_confidence = parsed.confidence
    deal.completeness_score = comp["score"]
    deal.missing_fields = json.dumps(comp["missing"], ensure_ascii=False)
    deal.next_steps = json.dumps(steps, ensure_ascii=False)
    deal.deal_probability = prob
    deal.calculated_price = econ["price"]
    deal.calculated_cost = econ["cost"]
    deal.calculated_profit = econ["profit"]
    deal.calculated_margin = econ["margin"]
    deal.draft_reply = f"{draft} ({prob_reason})"
    deal.warnings = json.dumps(warns, ensure_ascii=False)
    if deal.final_price is not None and deal.final_cost is not None:
        deal.final_profit = round(deal.final_price - deal.final_cost, 2)

    db.add(DealSnapshot(
        deal=deal,
        source="recalculate",
        calculated_price=deal.calculated_price,
        calculated_cost=deal.calculated_cost,
        calculated_profit=deal.calculated_profit,
        deal_probability=deal.deal_probability,
        completeness_score=deal.completeness_score,
        missing_fields=deal.missing_fields,
        next_steps=deal.next_steps,
    ))
    db.add(DealEvent(deal=deal, event_type="analysis", field_name=None, old_value=None, new_value=None, comment="Deal analyzed/recalculated"))
    db.commit()
    db.refresh(deal)
    return deal
