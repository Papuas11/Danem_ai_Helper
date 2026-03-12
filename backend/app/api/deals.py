from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Deal, DealEvent, DealSnapshot
from app.schemas.common import Message
from app.schemas.deals import (
    AnalyzeRequest,
    DealCreate,
    DealEventRead,
    DealRead,
    DealSnapshotRead,
    DealUpdate,
    RecalculateRequest,
)
from app.services.analysis import similar_deals
from app.services.deal_engine import run_analysis

router = APIRouter(prefix="/api", tags=["deals"])


@router.get("/deals", response_model=list[DealRead])
def list_deals(db: Session = Depends(get_db)):
    return db.query(Deal).order_by(Deal.updated_at.desc()).all()


@router.post("/deals", response_model=DealRead)
def create_deal(payload: DealCreate, db: Session = Depends(get_db)):
    deal = Deal(**payload.model_dump())
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return run_analysis(db, deal)


@router.get("/deals/{deal_id}", response_model=DealRead)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    return deal


@router.put("/deals/{deal_id}", response_model=DealRead)
def update_deal(deal_id: int, payload: DealUpdate, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(deal, k, v)
    db.commit()
    db.refresh(deal)
    return run_analysis(db, deal)


@router.post("/deals/analyze", response_model=DealRead)
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    deal = Deal(title=payload.title, input_text=payload.input_text)
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return run_analysis(db, deal)


@router.post("/deals/{deal_id}/recalculate", response_model=DealRead)
def recalculate(deal_id: int, payload: RecalculateRequest, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(deal, k, v)
        db.add(DealEvent(deal_id=deal.id, event_type="manual_edit", field_name=k, old_value=None, new_value=str(v), comment="Manual edit before recalculation"))
    db.commit()
    return run_analysis(db, deal)


@router.post("/deals/{deal_id}/finalize", response_model=DealRead)
def finalize(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    deal.status = "finalized"
    deal.price_confirmed = True
    if deal.final_price is not None and deal.final_cost is not None:
        deal.final_profit = round(deal.final_price - deal.final_cost, 2)
    db.add(DealEvent(deal_id=deal.id, event_type="finalize", field_name="status", old_value="draft", new_value="finalized", comment="Deal finalized"))
    db.commit()
    db.refresh(deal)
    return deal


@router.get("/deals/{deal_id}/events", response_model=list[DealEventRead])
def events(deal_id: int, db: Session = Depends(get_db)):
    return db.query(DealEvent).filter(DealEvent.deal_id == deal_id).order_by(DealEvent.created_at.desc()).all()


@router.get("/deals/{deal_id}/snapshots", response_model=list[DealSnapshotRead])
def snapshots(deal_id: int, db: Session = Depends(get_db)):
    return db.query(DealSnapshot).filter(DealSnapshot.deal_id == deal_id).order_by(DealSnapshot.created_at.desc()).all()


@router.get("/deals/{deal_id}/similar", response_model=list[DealRead])
def get_similar(deal_id: int, db: Session = Depends(get_db)):
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(404, "Deal not found")
    matches = similar_deals(db, deal.parsed_instrument_name, deal.parsed_service_type)
    return [d for d in matches if d.id != deal.id][:5]


@router.get("/internet-enrichment-mode", response_model=Message)
def internet_mode():
    return Message(message="Internet enrichment scaffolded; default mode OFF and no auto-write to DB.")
