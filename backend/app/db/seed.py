from sqlalchemy.orm import Session

from app.models.deal import Deal
from app.models.instrument import Instrument, InstrumentAlias, InstrumentService
from app.services.analysis_service import parse_text
from app.utils.json import dumps_list
from app.utils.text import normalize_text


def seed_data(db: Session):
    if db.query(Instrument).count() == 0:
        manometer = Instrument(name="Manometer", category="Pressure", status="active")
        pyrometer = Instrument(name="Pyrometer", category="Temperature", status="active")
        thermometer = Instrument(name="Thermometer", category="Temperature", status="active")
        db.add_all([manometer, pyrometer, thermometer])
        db.flush()

        for alias in ["манометр", "манометра", "манометры", "манометров", "pressure gauge", "gauge"]:
            db.add(InstrumentAlias(instrument_id=manometer.id, alias=alias, normalized_alias=normalize_text(alias)))

        db.add_all(
            [
                InstrumentService(
                    instrument_id=manometer.id,
                    service_type="calibration",
                    unit_type="per_item",
                    base_price=1200,
                    base_cost=700,
                    onsite_available=True,
                    onsite_price=1500,
                    onsite_cost=900,
                    required_client_data=dumps_list(["количество", "тип услуги", "выезд"]),
                    issued_documents=dumps_list(["certificate"]),
                    status="active",
                ),
                InstrumentService(
                    instrument_id=pyrometer.id,
                    service_type="verification",
                    unit_type="per_item",
                    base_price=1400,
                    base_cost=850,
                    onsite_available=False,
                    required_client_data=dumps_list(["количество", "тип услуги"]),
                    issued_documents=dumps_list(["verification report"]),
                    status="active",
                ),
                InstrumentService(
                    instrument_id=thermometer.id,
                    service_type="repair",
                    unit_type="per_item",
                    base_price=2000,
                    base_cost=1300,
                    onsite_available=True,
                    onsite_price=1800,
                    onsite_cost=1100,
                    required_client_data=dumps_list(["количество", "тип услуги", "описание неисправности"]),
                    issued_documents=dumps_list(["repair act"]),
                    status="draft",
                ),
            ]
        )
        db.commit()

    if db.query(Deal).count() == 0:
        examples = [
            "Нужна калибровка 3 манометров срочно без выезда",
            "Просим поверку 2 pyrometer, возможен выезд",
            "Ремонт thermometer 1 шт, срочно",
        ]
        for idx, text in enumerate(examples, start=1):
            parsed, _ = parse_text(db, text)
            db.add(
                Deal(
                    title=f"Seed deal {idx}",
                    input_text=text,
                    parsed_instrument_name=parsed.instrument_name,
                    parsed_service_type=parsed.service_type,
                    parsed_quantity=parsed.quantity,
                    parsed_onsite=parsed.onsite,
                    parsed_urgency=parsed.urgency,
                    ai_confidence=parsed.confidence,
                    completeness_score=50,
                    deal_probability=45,
                    missing_fields=dumps_list(["контакт клиента"]),
                    next_steps=dumps_list(["Уточнить детали", "Подготовить КП", "Отправить предложение"]),
                    calculated_price=3000,
                    calculated_cost=1800,
                    calculated_profit=1200,
                    calculated_margin=40,
                    final_price=3200,
                    final_cost=1900,
                    final_profit=1300,
                    deviation_reason_tag="urgency",
                    deviation_reason_text="Срочный срок",
                )
            )
        db.commit()
