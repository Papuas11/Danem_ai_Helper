import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.deal import Deal, DealEvent, DealSnapshot
from app.schemas.deal import (
    DealAnalyzeRequest,
    DealCreate,
    DealEventRead,
    DealRead,
    DealRecalculateRequest,
    DealSnapshotRead,
    DealUpdate,
)
from app.services.analysis_service import (
    calculate_economics,
    completeness,
    draft_reply,
    find_service,
    find_similar_deals,
    next_steps,
    parse_text,
    probability_score,
    warnings_list,
)
from app.utils.json import dumps_list, loads_list

router = APIRouter(prefix="/api", tags=["deals"])


def save_event(db: Session, deal_id: int, event_type: str, field_name: str | None = None, old_value: str | None = None, new_value: str | None = None, comment: str | None = None):
    db.add(DealEvent(deal_id=deal_id, event_type=event_type, field_name=field_name, old_value=old_value, new_value=new_value, comment=comment))


def save_snapshot(db: Session, deal: Deal, source: str):
    db.add(
        DealSnapshot(
            deal_id=deal.id,
            source=source,
            calculated_price=deal.calculated_price,
            calculated_cost=deal.calculated_cost,
            calculated_profit=deal.calculated_profit,
            deal_probability=deal.deal_probability,
            completeness_score=deal.completeness_score,
            missing_fields=deal.missing_fields,
            next_steps=deal.next_steps,
        )
    )


def to_read(db: Session, deal: Deal) -> DealRead:
    similar = find_similar_deals(db, deal.parsed_instrument_name, deal.parsed_service_type, limit=5)
    similar_items = [
        {
            "id": d.id,
            "instrument": d.parsed_instrument_name,
            "service": d.parsed_service_type,
            "calculated_price": d.calculated_price,
            "final_price": d.final_price,
            "deviation": (d.final_price - d.calculated_price) if d.final_price and d.calculated_price else None,
            "reason": d.deviation_reason_tag,
        }
        for d in similar
        if d.id != deal.id
    ][:5]
    warnings = warnings_list(
        parse_text(db, deal.input_text),
        {"margin": deal.calculated_margin},
        find_service(db, deal.parsed_instrument_name, deal.parsed_service_type),
        loads_list(deal.missing_fields),
        deal.final_price,
        deal.calculated_price,
    )
    return DealRead(
        id=deal.id,
        title=deal.title,
        client_name=deal.client_name,
        input_text=deal.input_text,
        manager_notes=deal.manager_notes,
        status=deal.status,
        deal_probability=deal.deal_probability,
        completeness_score=deal.completeness_score,
        parsed_instrument_name=deal.parsed_instrument_name,
        parsed_service_type=deal.parsed_service_type,
        parsed_quantity=deal.parsed_quantity,
        parsed_onsite=deal.parsed_onsite,
        parsed_urgency=deal.parsed_urgency,
        ai_confidence=deal.ai_confidence,
        missing_fields=loads_list(deal.missing_fields),
        next_steps=loads_list(deal.next_steps),
        draft_reply=deal.draft_reply,
        calculated_price=deal.calculated_price,
        calculated_cost=deal.calculated_cost,
        calculated_profit=deal.calculated_profit,
        calculated_margin=deal.calculated_margin,
        final_price=deal.final_price,
        final_cost=deal.final_cost,
        final_profit=deal.final_profit,
        price_confirmed=deal.price_confirmed,
        deviation_reason_tag=deal.deviation_reason_tag,
        deviation_reason_text=deal.deviation_reason_text,
        warnings=warnings,
        similar_deals=similar_items,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
    )


def run_analysis(db: Session, deal: Deal):
    parsed = parse_text(db, deal.input_text)
    service = find_service(db, parsed.instrument_name, parsed.service_type)
    required = loads_list(service.required_client_data) if service and service.required_client_data else ["количество", "тип услуги"]
    known_map = {
        "количество": parsed.quantity,
        "тип услуги": parsed.service_type,
        "выезд": parsed.onsite if parsed.onsite != "unknown" else None,
        "прибор": parsed.instrument_name,
    }
    completeness_score, missing = completeness(required, known_map)
    economics = calculate_economics(service, parsed.quantity, parsed.onsite)
    has_similar = len(find_similar_deals(db, parsed.instrument_name, parsed.service_type, limit=3)) > 0
    prob, _ = probability_score(parsed, completeness_score, economics.get("margin"), has_similar)
    warn = warnings_list(parsed, economics, service, missing, deal.final_price, economics.get("price"))
    steps = next_steps(missing, parsed, warn)

    deal.parsed_instrument_name = parsed.instrument_name
    deal.parsed_service_type = parsed.service_type
    deal.parsed_quantity = parsed.quantity
    deal.parsed_onsite = parsed.onsite
    deal.parsed_urgency = parsed.urgency
    deal.ai_confidence = parsed.confidence
    deal.completeness_score = completeness_score
    deal.missing_fields = dumps_list(missing)
    deal.calculated_price = economics.get("price")
    deal.calculated_cost = economics.get("cost")
    deal.calculated_profit = economics.get("profit")
    deal.calculated_margin = economics.get("margin")
    deal.deal_probability = prob
    deal.next_steps = dumps_list(steps)
    deal.draft_reply = draft_reply(parsed, missing, economics.get("price"))


@router.get("/deals", response_model=list[DealRead])
def list_deals(db: Session = Depends(get_db)):
    return [to_read(db, d) for d in db.query(Deal).order_by(Deal.updated_at.desc()).all()]


@router.post("/deals", response_model=DealRead)
def create_deal(payload: DealCreate, db: Session = Depends(get_db)):
    deal = Deal(title=payload.title, client_name=payload.client_name, input_text=payload.input_text)
    db.add(deal)
    db.flush()
    run_analysis(db, deal)
    save_event(db, deal.id, "create", comment="Deal created")
    save_snapshot(db, deal, "create")
    db.commit()
    db.refresh(deal)
    return to_read(db, deal)


@router.get("/deals/{deal_id}", response_model=DealRead)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return to_read(db, deal)


@router.put("/deals/{deal_id}", response_model=DealRead)
def update_deal(deal_id: int, payload: DealUpdate, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        old = getattr(deal, k)
        setattr(deal, k, v)
        if str(old) != str(v):
            save_event(db, deal.id, "update", field_name=k, old_value=str(old), new_value=str(v))
    run_analysis(db, deal)
    if deal.final_price is not None and deal.final_cost is not None:
        deal.final_profit = deal.final_price - deal.final_cost
    save_snapshot(db, deal, "update")
    db.commit()
    db.refresh(deal)
    return to_read(db, deal)


@router.post("/deals/analyze", response_model=DealRead)
def analyze(payload: DealAnalyzeRequest, db: Session = Depends(get_db)):
    deal = Deal(title=payload.title, client_name=payload.client_name, input_text=payload.input_text)
    db.add(deal)
    db.flush()
    run_analysis(db, deal)
    save_event(db, deal.id, "analyze", comment="Initial analysis")
    save_snapshot(db, deal, "analyze")
    db.commit()
    db.refresh(deal)
    return to_read(db, deal)


@router.post("/deals/{deal_id}/recalculate", response_model=DealRead)
def recalculate(deal_id: int, payload: DealRecalculateRequest, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(deal, k, v)
        save_event(db, deal.id, "manual_edit", field_name=k, new_value=str(v))
    if deal.final_price is not None and deal.final_cost is not None:
        deal.final_profit = deal.final_price - deal.final_cost
    run_analysis(db, deal)
    save_snapshot(db, deal, "recalculate")
    db.commit()
    db.refresh(deal)
    return to_read(db, deal)


@router.post("/deals/{deal_id}/finalize", response_model=DealRead)
def finalize(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    deal.status = "won"
    deal.price_confirmed = True
    if deal.final_price is not None and deal.final_cost is not None:
        deal.final_profit = deal.final_price - deal.final_cost
    save_event(db, deal.id, "finalize", comment="Deal finalized")
    save_snapshot(db, deal, "finalize")
    db.commit()
    db.refresh(deal)
    return to_read(db, deal)


@router.get("/deals/{deal_id}/events", response_model=list[DealEventRead])
def deal_events(deal_id: int, db: Session = Depends(get_db)):
    return db.query(DealEvent).filter(DealEvent.deal_id == deal_id).order_by(DealEvent.created_at.desc()).all()


@router.get("/deals/{deal_id}/snapshots", response_model=list[DealSnapshotRead])
def deal_snapshots(deal_id: int, db: Session = Depends(get_db)):
    return db.query(DealSnapshot).filter(DealSnapshot.deal_id == deal_id).order_by(DealSnapshot.created_at.desc()).all()


@router.get("/deals/{deal_id}/similar")
def similar(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    matches = find_similar_deals(db, deal.parsed_instrument_name, deal.parsed_service_type, limit=5)
    return [to_read(db, d).model_dump() for d in matches if d.id != deal.id]
