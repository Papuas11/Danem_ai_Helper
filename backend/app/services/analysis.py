from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.models import Deal, Instrument, InstrumentAlias, InstrumentService
from app.utils.text import extract_quantity, normalize_text


@dataclass
class ParseResult:
    instrument: Instrument | None
    service: InstrumentService | None
    quantity: int | None
    onsite: str
    urgency: str
    confidence: float
    status: str


def parse_text(db: Session, text: str) -> ParseResult:
    normalized = normalize_text(text)
    instruments = db.query(Instrument).filter(Instrument.status != "archived").all()
    best_instrument = None
    score = 0.0

    for instrument in instruments:
        name_match = instrument.name.lower() in normalized
        alias_match = db.query(InstrumentAlias).filter(
            InstrumentAlias.instrument_id == instrument.id
        ).all()
        alias_hit = any(a.normalized_alias in normalized for a in alias_match)
        current = 0.0
        if name_match:
            current += 0.5
        if alias_hit:
            current += 0.35
        if current > score:
            score = current
            best_instrument = instrument

    quantity = extract_quantity(normalized)
    onsite = "yes" if any(word in normalized for word in ["onsite", "on-site", "выезд"]) else "no" if "no onsite" in normalized or "без выезда" in normalized else "unknown"
    urgency = "yes" if any(word in normalized for word in ["urgent", "asap", "срочно"]) else "unknown"

    service = None
    if best_instrument:
        services = db.query(InstrumentService).filter(InstrumentService.instrument_id == best_instrument.id).all()
        for s in services:
            if s.service_type.lower() in normalized:
                service = s
                break
        if not service and services:
            service = services[0]

    if service:
        score += 0.15
    if quantity:
        score += 0.1
    confidence = min(1.0, round(score, 2))
    status = "parsed" if best_instrument else "needs_review"

    return ParseResult(best_instrument, service, quantity, onsite, urgency, confidence, status)


def calculate_economics(service: InstrumentService | None, quantity: int | None, onsite: str) -> dict:
    qty = quantity or 1
    prelim = False
    if not service:
        prelim = True
        return {
            "price": 0.0,
            "cost": 0.0,
            "profit": 0.0,
            "margin": 0.0,
            "notes": "No service matched; preliminary values only.",
            "preliminary": prelim,
        }

    multiplier = qty if service.unit_type == "per_item" else 1
    price = service.base_price * multiplier
    cost = service.base_cost * multiplier
    note = ""

    if onsite == "yes":
        if service.onsite_available:
            price += service.onsite_price
            cost += service.onsite_cost
            note = "Onsite requested and added."
        else:
            note = "Onsite requested but not available for this service."
            prelim = True

    profit = price - cost
    margin = (profit / price * 100.0) if price > 0 else 0.0
    return {
        "price": round(price, 2),
        "cost": round(cost, 2),
        "profit": round(profit, 2),
        "margin": round(margin, 2),
        "notes": note,
        "preliminary": prelim,
    }


def completeness(parsed: ParseResult, service: InstrumentService | None) -> dict:
    required = ["instrument", "service", "quantity"]
    known = []
    missing = []

    if parsed.instrument:
        known.append("instrument")
    else:
        missing.append("instrument")

    if service:
        known.append("service")
    else:
        missing.append("service")

    if parsed.quantity:
        known.append("quantity")
    else:
        missing.append("quantity")

    if parsed.onsite != "unknown":
        known.append("onsite")
    else:
        missing.append("onsite")

    if service and service.required_client_data:
        for item in [x.strip() for x in service.required_client_data.split(",") if x.strip()]:
            required.append(item)
            missing.append(item)

    score = round((len(known) / max(len(required), 1)) * 100, 2)
    return {"score": score, "known": known, "missing": missing}


def probability(parsed: ParseResult, completeness_score: float, economics: dict, similar_success_count: int) -> tuple[float, str]:
    p = 35.0
    reasons = []
    if parsed.instrument:
        p += 15
        reasons.append("instrument matched")
    if parsed.service:
        p += 10
        reasons.append("service identified")
    if parsed.quantity:
        p += 5
    p += completeness_score * 0.2
    if parsed.onsite == "yes" and parsed.service and not parsed.service.onsite_available:
        p -= 20
        reasons.append("onsite not feasible")
    if parsed.confidence < 0.5:
        p -= 10
        reasons.append("low AI confidence")
    if economics["margin"] < 20:
        p -= 8
        reasons.append("low margin")
    p += min(similar_success_count * 3, 9)
    p = max(5.0, min(95.0, round(p, 2)))
    return p, ", ".join(reasons) if reasons else "baseline scoring"


def next_steps(missing: list[str], onsite: str, confidence: float) -> list[str]:
    steps = []
    if missing:
        steps.append(f"Request missing data: {', '.join(missing[:3])}.")
    else:
        steps.append("Confirm parsed details with client.")

    if onsite == "unknown":
        steps.append("Clarify onsite requirement and access conditions.")
    elif onsite == "yes":
        steps.append("Verify onsite slot availability with operations.")
    else:
        steps.append("Prepare remote/in-lab workflow timeline.")

    if confidence < 0.5:
        steps.append("Manually review parsed instrument and service before quote.")
    else:
        steps.append("Send quote draft and ask for confirmation.")

    while len(steps) < 3:
        steps.append("Log update in deal history.")
    return steps[:3]


def draft_reply(missing: list[str], price: float) -> str:
    if missing:
        return f"Thank you for your request. To finalize the offer, please share: {', '.join(missing[:4])}. Estimated budget starts near {price:.2f}."
    return f"Thank you for the details. We prepared a draft offer with estimated price {price:.2f}. Please confirm to proceed."


def warnings(parsed: ParseResult, economics: dict, missing: list[str], final_price: float | None) -> list[str]:
    result = []
    if economics["margin"] < 15:
        result.append("Low margin warning")
    if missing:
        result.append("Missing required data")
    if parsed.confidence < 0.5:
        result.append("Low AI confidence")
    if parsed.onsite == "yes" and parsed.service and not parsed.service.onsite_available:
        result.append("Onsite not available")
    if final_price is not None and economics["price"] > 0 and abs(final_price - economics["price"]) / economics["price"] > 0.25:
        result.append("Final price strongly differs from estimate")
    return result


def similar_deals(db: Session, instrument_name: str | None, service_type: str | None, limit: int = 5) -> list[Deal]:
    query = db.query(Deal)
    if instrument_name:
        query = query.filter(Deal.parsed_instrument_name == instrument_name)
    if service_type:
        query = query.filter(Deal.parsed_service_type == service_type)
    return query.order_by(Deal.updated_at.desc()).limit(limit).all()
