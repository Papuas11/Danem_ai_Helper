from sqlalchemy.orm import Session
from app.models.models import Deal, Instrument, InstrumentAlias, InstrumentService
from app.utils.text import normalize_text


def seed_data(db: Session):
    if db.query(Instrument).count() > 0:
        return

    manometer = Instrument(name="Manometer", category="Pressure", status="active")
    pyrometer = Instrument(name="Pyrometer", category="Temperature", status="active")
    thermometer = Instrument(name="Thermometer", category="Temperature", status="active")
    db.add_all([manometer, pyrometer, thermometer])
    db.flush()

    for a in ["манометр", "манометра", "манометры", "манометров", "pressure gauge", "gauge"]:
        db.add(InstrumentAlias(instrument_id=manometer.id, alias=a, normalized_alias=normalize_text(a)))
    db.add(InstrumentAlias(instrument_id=pyrometer.id, alias="пирометр", normalized_alias=normalize_text("пирометр")))
    db.add(InstrumentAlias(instrument_id=thermometer.id, alias="термометр", normalized_alias=normalize_text("термометр")))

    db.add_all([
        InstrumentService(
            instrument_id=manometer.id,
            service_type="calibration",
            unit_type="per_item",
            base_price=120.0,
            base_cost=70.0,
            onsite_available=True,
            onsite_price=60.0,
            onsite_cost=30.0,
            required_client_data="model,accuracy,last calibration date",
            issued_documents="Calibration certificate",
        ),
        InstrumentService(
            instrument_id=pyrometer.id,
            service_type="verification",
            unit_type="per_item",
            base_price=140.0,
            base_cost=85.0,
            onsite_available=False,
            required_client_data="model,temperature range",
            issued_documents="Verification protocol",
        ),
        InstrumentService(
            instrument_id=thermometer.id,
            service_type="diagnostics",
            unit_type="per_item",
            base_price=90.0,
            base_cost=50.0,
            onsite_available=True,
            onsite_price=40.0,
            onsite_cost=20.0,
            required_client_data="model,sensor type",
            issued_documents="Diagnostic report",
        ),
    ])

    db.add_all([
        Deal(title="Manometer urgent request", input_text="Need calibration of 2 pressure gauge units, urgent", parsed_instrument_name="Manometer", parsed_service_type="calibration", calculated_price=300, final_price=320, final_cost=190),
        Deal(title="Pyrometer standard", input_text="Verification for pyrometer model P500", parsed_instrument_name="Pyrometer", parsed_service_type="verification", calculated_price=140, final_price=140, final_cost=90),
        Deal(title="Thermometer onsite", input_text="Diagnostics of 3 thermometers onsite", parsed_instrument_name="Thermometer", parsed_service_type="diagnostics", calculated_price=310, final_price=280, final_cost=200),
    ])

    db.commit()
