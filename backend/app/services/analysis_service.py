from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.deal import Deal
from app.models.instrument import Instrument, InstrumentAlias, InstrumentService
from app.utils.text import normalize_text


@dataclass
class ParsedResult:
    instrument_name: str | None
    service_type: str | None
    quantity: int | None
    onsite: str
    urgency: str
    confidence: float
    status: str


def parse_text(db: Session, text: str) -> ParsedResult:
    normalized = normalize_text(text)
    instrument_name = None
    service_type = None
    confidence = 0.2

    aliases = db.query(InstrumentAlias).options(selectinload(InstrumentAlias.instrument)).all()
    for alias in aliases:
        if alias.normalized_alias in normalized:
            instrument_name = alias.instrument.name
            confidence += 0.35
            break

    if not instrument_name:
        instruments = db.query(Instrument).all()
        for inst in instruments:
            if normalize_text(inst.name) in normalized:
                instrument_name = inst.name
                confidence += 0.25
                break

    service_keywords = {
        "калибров": "calibration",
        "поверк": "verification",
        "ремонт": "repair",
        "calibration": "calibration",
        "verification": "verification",
        "repair": "repair",
    }
    for key, mapped in service_keywords.items():
        if key in normalized:
            service_type = mapped
            confidence += 0.2
            break

    quantity = None
    for token in normalized.split():
        if token.isdigit():
            quantity = int(token)
            confidence += 0.1
            break

    onsite = "unknown"
    if "без выезда" in normalized or "remote" in normalized:
        onsite = "no"
        confidence += 0.1
    elif "выезд" in normalized or "onsite" in normalized:
        onsite = "yes"
        confidence += 0.1

    urgency = "unknown"
    if "срочно" in normalized or "urgent" in normalized:
        urgency = "yes"
        confidence += 0.1
    elif "не срочно" in normalized:
        urgency = "no"

    status = "parsed" if instrument_name or service_type else "needs_review"
    return ParsedResult(
        instrument_name=instrument_name,
        service_type=service_type,
        quantity=quantity,
        onsite=onsite,
        urgency=urgency,
        confidence=max(0.0, min(confidence, 0.99)),
        status=status,
    )


def calculate_economics(service: InstrumentService | None, quantity: int | None, onsite: str) -> dict:
    qty = quantity or 1
    preliminary = False
    if not service:
        return {
            "price": None,
            "cost": None,
            "profit": None,
            "margin": None,
            "preliminary": True,
            "onsite_note": "Услуга не найдена, расчёт невозможен",
        }

    multiplier = qty if service.unit_type == "per_item" else 1
    price = service.base_price * multiplier
    cost = service.base_cost * multiplier
    onsite_note = "Выезд не применён"

    if onsite == "yes":
        if service.onsite_available:
            price += service.onsite_price or 0
            cost += service.onsite_cost or 0
            onsite_note = "Добавлена стоимость выезда"
        else:
            onsite_note = "Выезд запрошен, но недоступен"
            preliminary = True

    profit = price - cost
    margin = (profit / price * 100) if price else 0
    return {
        "price": round(price, 2),
        "cost": round(cost, 2),
        "profit": round(profit, 2),
        "margin": round(margin, 2),
        "preliminary": preliminary,
        "onsite_note": onsite_note,
    }


def completeness(required: list[str], known: dict) -> tuple[float, list[str]]:
    if not required:
        return 100.0, []
    missing = [field for field in required if not known.get(field)]
    filled = len(required) - len(missing)
    return round((filled / len(required)) * 100, 2), missing


def probability_score(parsed: ParsedResult, completeness_score: float, margin: float | None, has_similar_success: bool) -> tuple[float, str]:
    score = 25.0
    factors = []
    if parsed.instrument_name:
        score += 20
        factors.append("инструмент найден")
    if parsed.service_type:
        score += 15
        factors.append("услуга найдена")
    if parsed.quantity:
        score += 8
        factors.append("количество указано")
    score += completeness_score * 0.25
    factors.append(f"полнота {completeness_score:.0f}%")
    if parsed.confidence < 0.5:
        score -= 15
        factors.append("низкая уверенность")
    if margin is not None and margin < 15:
        score -= 10
        factors.append("низкая маржа")
    if has_similar_success:
        score += 8
        factors.append("есть похожие успешные сделки")
    return max(5, min(95, round(score, 2))), ", ".join(factors)


def next_steps(missing_fields: list[str], parsed: ParsedResult, warnings: list[str]) -> list[str]:
    steps = []
    if missing_fields:
        steps.append(f"Запросить у клиента: {', '.join(missing_fields[:2])}")
    else:
        steps.append("Подтвердить сроки и запустить подготовку КП")

    if parsed.onsite == "unknown":
        steps.append("Уточнить необходимость выезда инженера")
    elif parsed.onsite == "yes":
        steps.append("Подтвердить адрес и окно времени для выезда")
    else:
        steps.append("Подтвердить передачу приборов в лабораторию")

    if warnings:
        steps.append("Согласовать риски и скорректировать предложение")
    else:
        steps.append("Отправить клиенту предварительное КП")

    return (steps + ["Зафиксировать договорённости в CRM"])[:3]


def draft_reply(parsed: ParsedResult, missing_fields: list[str], price: float | None) -> str:
    service = parsed.service_type or "услуге"
    instrument = parsed.instrument_name or "прибору"
    price_text = f"Предварительная стоимость: {price:.2f}. " if price else ""
    if missing_fields:
        ask = ", ".join(missing_fields)
        return f"Спасибо за запрос по {service} ({instrument}). {price_text}Для точного КП уточните, пожалуйста: {ask}."
    return f"Спасибо за запрос по {service} ({instrument}). {price_text}Готовы направить коммерческое предложение и согласовать запуск работ."


def warnings_list(parsed: ParsedResult, economics: dict, service: InstrumentService | None, missing_fields: list[str], final_price: float | None, calc_price: float | None) -> list[str]:
    warnings = []
    if economics.get("margin") is not None and economics["margin"] < 15:
        warnings.append("Низкая маржа")
    if missing_fields:
        warnings.append("Не хватает обязательных данных")
    if parsed.confidence < 0.5:
        warnings.append("Низкая уверенность AI")
    if parsed.onsite == "yes" and service and not service.onsite_available:
        warnings.append("Выезд недоступен")
    if service and service.status == "draft":
        warnings.append("Услуга в статусе draft")
    if final_price and calc_price and abs(final_price - calc_price) / max(calc_price, 1) > 0.25:
        warnings.append("Фактическая цена сильно отличается от расчётной")
    return warnings


def find_service(db: Session, instrument_name: str | None, service_type: str | None) -> InstrumentService | None:
    if not instrument_name:
        return None
    query = db.query(InstrumentService).join(Instrument).filter(Instrument.name == instrument_name)
    if service_type:
        query = query.filter(func.lower(InstrumentService.service_type) == service_type.lower())
    return query.first()


def find_similar_deals(db: Session, instrument_name: str | None, service_type: str | None, limit: int = 5) -> list[Deal]:
    query = db.query(Deal)
    if instrument_name:
        query = query.filter(Deal.parsed_instrument_name == instrument_name)
    if service_type:
        query = query.filter(Deal.parsed_service_type == service_type)
    return query.order_by(Deal.updated_at.desc()).limit(limit).all()
