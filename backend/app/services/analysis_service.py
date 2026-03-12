from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.deal import Deal
from app.models.instrument import Instrument, InstrumentAlias, InstrumentService
from app.services.ai_prompts import (
    build_deviation_analysis_prompt,
    build_draft_reply_prompt,
    build_estimate_review_prompt,
    build_missing_data_prompt,
    build_parse_prompt,
    build_probability_explanation_prompt,
    build_risk_warnings_prompt,
    build_similar_deals_prompt,
    build_three_steps_prompt,
)
from app.services.openai_service import openai_service
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
    missing_details: list[str]
    implied_intent: str | None


@dataclass
class AIUsage:
    ai_used: bool = False
    ai_fallback_used: bool = False

    def merge(self, ai_used: bool, fallback_used: bool):
        self.ai_used = self.ai_used or ai_used
        self.ai_fallback_used = self.ai_fallback_used or fallback_used


def parse_text_rule(db: Session, text: str) -> ParsedResult:
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
        missing_details=[],
        implied_intent=None,
    )


def parse_text(db: Session, text: str) -> tuple[ParsedResult, AIUsage]:
    fallback = parse_text_rule(db, text)
    usage = AIUsage()

    instruments = [r.name for r in db.query(Instrument).all()]
    service_types = [r[0] for r in db.query(InstrumentService.service_type).distinct().all() if r[0]]
    ai = openai_service.ask_json(
        build_parse_prompt(text=text, instruments=instruments, service_types=service_types),
        fallback={
            "instrument": fallback.instrument_name,
            "service_type": fallback.service_type,
            "quantity": fallback.quantity,
            "onsite": fallback.onsite,
            "urgency": fallback.urgency,
            "missing_details": fallback.missing_details,
            "implied_intent": fallback.implied_intent,
            "confidence": fallback.confidence,
        },
    )
    usage.merge(ai.ai_used, ai.fallback_used)

    parsed = ParsedResult(
        instrument_name=ai.data.get("instrument") or fallback.instrument_name,
        service_type=ai.data.get("service_type") or fallback.service_type,
        quantity=ai.data.get("quantity") if isinstance(ai.data.get("quantity"), int) else fallback.quantity,
        onsite=ai.data.get("onsite") if ai.data.get("onsite") in {"yes", "no", "unknown"} else fallback.onsite,
        urgency=ai.data.get("urgency") if ai.data.get("urgency") in {"yes", "no", "unknown"} else fallback.urgency,
        confidence=float(ai.data.get("confidence", fallback.confidence) or fallback.confidence),
        status="parsed" if (ai.data.get("instrument") or ai.data.get("service_type") or fallback.instrument_name or fallback.service_type) else "needs_review",
        missing_details=ai.data.get("missing_details") if isinstance(ai.data.get("missing_details"), list) else [],
        implied_intent=ai.data.get("implied_intent"),
    )

    validated = validate_against_db(db, parsed)
    return validated, usage


def validate_against_db(db: Session, parsed: ParsedResult) -> ParsedResult:
    instrument_name = parsed.instrument_name
    if instrument_name:
        inst_exists = db.query(Instrument).filter(func.lower(Instrument.name) == instrument_name.lower()).first()
        if not inst_exists:
            alias = db.query(InstrumentAlias).options(selectinload(InstrumentAlias.instrument)).filter(func.lower(InstrumentAlias.alias) == instrument_name.lower()).first()
            instrument_name = alias.instrument.name if alias else None

    service_type = parsed.service_type
    if service_type:
        service_match = db.query(InstrumentService).filter(func.lower(InstrumentService.service_type) == service_type.lower()).first()
        if not service_match:
            service_type = None

    return ParsedResult(
        instrument_name=instrument_name,
        service_type=service_type,
        quantity=parsed.quantity,
        onsite=parsed.onsite,
        urgency=parsed.urgency,
        confidence=max(0.0, min(parsed.confidence, 0.99)),
        status=parsed.status,
        missing_details=parsed.missing_details,
        implied_intent=parsed.implied_intent,
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
        factors.append("низкая уверенность AI")
    if margin is not None and margin < 15:
        score -= 10
        factors.append("низкая маржа")
    if has_similar_success:
        score += 8
        factors.append("есть похожие успешные сделки")
    return max(5, min(95, round(score, 2))), ", ".join(factors)


def ai_missing_data(required: list[str], known: dict, parsed: ParsedResult, deal_stage: str, usage: AIUsage) -> tuple[list[str], list[str]]:
    base_missing = [field for field in required if not known.get(field)]
    ai = openai_service.ask_json(
        build_missing_data_prompt(
            {
                "required": required,
                "known": known,
                "parsed": parsed.__dict__,
                "stage": deal_stage,
            }
        ),
        fallback={"missing_fields": base_missing, "suggestions": []},
    )
    usage.merge(ai.ai_used, ai.fallback_used)
    missing = ai.data.get("missing_fields") if isinstance(ai.data.get("missing_fields"), list) else base_missing
    suggestions = ai.data.get("suggestions") if isinstance(ai.data.get("suggestions"), list) else []
    return missing, suggestions


def next_steps(missing_fields: list[str], parsed: ParsedResult, warnings: list[str], similar_deals: list[Deal], deal_stage: str, usage: AIUsage) -> list[str]:
    fallback = []
    if missing_fields:
        fallback.append(f"Запросить у клиента: {', '.join(missing_fields[:2])}")
    else:
        fallback.append("Подтвердить сроки и запустить подготовку КП")

    if parsed.onsite == "unknown":
        fallback.append("Уточнить необходимость выезда инженера")
    elif parsed.onsite == "yes":
        fallback.append("Подтвердить адрес и окно времени для выезда")
    else:
        fallback.append("Подтвердить передачу приборов в лабораторию")

    if warnings:
        fallback.append("Согласовать риски и скорректировать предложение")
    else:
        fallback.append("Отправить клиенту предварительное КП")

    ai = openai_service.ask_json(
        build_three_steps_prompt(
            {
                "missing_fields": missing_fields,
                "parsed": parsed.__dict__,
                "warnings": warnings,
                "deal_stage": deal_stage,
                "similar_deals": [
                    {
                        "id": d.id,
                        "instrument": d.parsed_instrument_name,
                        "service": d.parsed_service_type,
                        "final_price": d.final_price,
                    }
                    for d in similar_deals[:5]
                ],
            }
        ),
        fallback={"steps": fallback[:3]},
    )
    usage.merge(ai.ai_used, ai.fallback_used)
    steps = ai.data.get("steps") if isinstance(ai.data.get("steps"), list) else fallback
    return (steps + ["Зафиксировать договорённости в CRM"])[:3]


def draft_reply(parsed: ParsedResult, missing_fields: list[str], price: float | None, onsite_possible: bool | None, usage: AIUsage) -> str:
    fallback = _draft_reply_fallback(parsed, missing_fields, price)
    ai = openai_service.ask_json(
        build_draft_reply_prompt(
            {
                "parsed": parsed.__dict__,
                "missing_fields": missing_fields,
                "preliminary_price": price,
                "onsite_possible": onsite_possible,
            }
        ),
        fallback={"draft_reply": fallback},
    )
    usage.merge(ai.ai_used, ai.fallback_used)
    return str(ai.data.get("draft_reply") or fallback)


def _draft_reply_fallback(parsed: ParsedResult, missing_fields: list[str], price: float | None) -> str:
    service = parsed.service_type or "услуге"
    instrument = parsed.instrument_name or "прибору"
    price_text = f"Предварительная стоимость: {price:.2f}. " if price else ""
    if missing_fields:
        ask = ", ".join(missing_fields)
        return f"Спасибо за запрос по {service} ({instrument}). {price_text}Для точного КП уточните, пожалуйста: {ask}."
    return f"Спасибо за запрос по {service} ({instrument}). {price_text}Готовы направить коммерческое предложение и согласовать запуск работ."


def warnings_list(parsed: ParsedResult, economics: dict, service: InstrumentService | None, missing_fields: list[str], final_price: float | None, calc_price: float | None, usage: AIUsage) -> list[str]:
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

    ai = openai_service.ask_json(
        build_risk_warnings_prompt(
            {
                "parsed": parsed.__dict__,
                "economics": economics,
                "missing_fields": missing_fields,
                "base_warnings": warnings,
            }
        ),
        fallback={"warnings": warnings},
    )
    usage.merge(ai.ai_used, ai.fallback_used)
    ai_warnings = ai.data.get("warnings") if isinstance(ai.data.get("warnings"), list) else []
    merged = []
    for item in warnings + ai_warnings:
        if isinstance(item, str) and item not in merged:
            merged.append(item)
    return merged


def probability_explanation(score: float, factors: str, parsed: ParsedResult, missing_fields: list[str], usage: AIUsage) -> str:
    fallback = f"Вероятность {score:.0f}% рассчитана по правилам: {factors}."
    ai = openai_service.ask_json(
        build_probability_explanation_prompt(
            {
                "score": score,
                "factors": factors,
                "parsed": parsed.__dict__,
                "missing_fields": missing_fields,
            }
        ),
        fallback={"explanation": fallback},
    )
    usage.merge(ai.ai_used, ai.fallback_used)
    return str(ai.data.get("explanation") or fallback)


def similar_deals_summary(similar: list[Deal], parsed: ParsedResult, usage: AIUsage) -> str:
    fallback = "Похожие сделки отсутствуют." if not similar else "Найдены похожие сделки, ориентируйтесь на их фактические отклонения."
    ai = openai_service.ask_json(
        build_similar_deals_prompt(
            {
                "parsed": parsed.__dict__,
                "similar_deals": [
                    {
                        "instrument": d.parsed_instrument_name,
                        "service": d.parsed_service_type,
                        "calc_price": d.calculated_price,
                        "final_price": d.final_price,
                        "deviation_reason": d.deviation_reason_tag,
                    }
                    for d in similar[:10]
                ],
            }
        ),
        fallback={"summary": fallback},
    )
    usage.merge(ai.ai_used, ai.fallback_used)
    return str(ai.data.get("summary") or fallback)


def estimate_review(economics: dict, similar: list[Deal], usage: AIUsage) -> dict:
    fallback = {
        "realism": "unknown",
        "likely_variance_note": "Используйте фактические данные для уточнения.",
        "caution_notes": [],
        "suggested_adjustment_note": None,
    }
    ai = openai_service.ask_json(
        build_estimate_review_prompt(
            {
                "economics": economics,
                "similar": [
                    {"calc": d.calculated_price, "final": d.final_price, "reason": d.deviation_reason_tag}
                    for d in similar[:10]
                ],
            }
        ),
        fallback=fallback,
    )
    usage.merge(ai.ai_used, ai.fallback_used)
    return {
        "realism": ai.data.get("realism", fallback["realism"]),
        "likely_variance_note": ai.data.get("likely_variance_note", fallback["likely_variance_note"]),
        "caution_notes": ai.data.get("caution_notes") if isinstance(ai.data.get("caution_notes"), list) else fallback["caution_notes"],
        "suggested_adjustment_note": ai.data.get("suggested_adjustment_note"),
    }


def deviation_analysis(deal: Deal, usage: AIUsage) -> dict | None:
    if deal.final_price is None or deal.calculated_price is None:
        return None
    fallback = {
        "summary": "Отклонение зафиксировано, требуется ручной разбор.",
        "root_causes": [],
        "db_review_recommendation": "Проверить причину отклонения вручную.",
        "should_influence_future_estimates": "maybe",
    }
    ai = openai_service.ask_json(
        build_deviation_analysis_prompt(
            {
                "calculated_price": deal.calculated_price,
                "calculated_cost": deal.calculated_cost,
                "final_price": deal.final_price,
                "final_cost": deal.final_cost,
                "final_profit": deal.final_profit,
                "deviation_reason_tag": deal.deviation_reason_tag,
                "deviation_reason_text": deal.deviation_reason_text,
            }
        ),
        fallback=fallback,
    )
    usage.merge(ai.ai_used, ai.fallback_used)
    return {
        "summary": ai.data.get("summary", fallback["summary"]),
        "root_causes": ai.data.get("root_causes") if isinstance(ai.data.get("root_causes"), list) else fallback["root_causes"],
        "db_review_recommendation": ai.data.get("db_review_recommendation", fallback["db_review_recommendation"]),
        "should_influence_future_estimates": ai.data.get("should_influence_future_estimates", fallback["should_influence_future_estimates"]),
    }


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
