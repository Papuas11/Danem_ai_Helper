from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.models import Instrument, InstrumentAlias, InstrumentService
from app.schemas.common import Message
from app.schemas.instruments import (
    AliasCreate,
    InstrumentCreate,
    InstrumentRead,
    InstrumentUpdate,
    ServiceCreate,
    ServiceRead,
)
from app.utils.text import normalize_text

router = APIRouter(prefix="/api", tags=["instruments"])


@router.get("/instruments", response_model=list[InstrumentRead])
def list_instruments(db: Session = Depends(get_db)):
    return db.query(Instrument).options(joinedload(Instrument.aliases), joinedload(Instrument.services)).all()


@router.post("/instruments", response_model=InstrumentRead)
def create_instrument(payload: InstrumentCreate, db: Session = Depends(get_db)):
    instrument = Instrument(**payload.model_dump())
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


@router.get("/instruments/{instrument_id}", response_model=InstrumentRead)
def get_instrument(instrument_id: int, db: Session = Depends(get_db)):
    item = db.query(Instrument).options(joinedload(Instrument.aliases), joinedload(Instrument.services)).filter(Instrument.id == instrument_id).first()
    if not item:
        raise HTTPException(404, "Instrument not found")
    return item


@router.put("/instruments/{instrument_id}", response_model=InstrumentRead)
def update_instrument(instrument_id: int, payload: InstrumentUpdate, db: Session = Depends(get_db)):
    item = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not item:
        raise HTTPException(404, "Instrument not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/instruments/{instrument_id}", response_model=Message)
def delete_instrument(instrument_id: int, db: Session = Depends(get_db)):
    item = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not item:
        raise HTTPException(404, "Instrument not found")
    item.status = "archived"
    db.commit()
    return Message(message="Instrument archived")


@router.post("/instruments/{instrument_id}/aliases", response_model=InstrumentRead)
def add_alias(instrument_id: int, payload: AliasCreate, db: Session = Depends(get_db)):
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(404, "Instrument not found")
    db.add(InstrumentAlias(instrument_id=instrument_id, alias=payload.alias, normalized_alias=normalize_text(payload.alias)))
    db.commit()
    return get_instrument(instrument_id, db)


@router.delete("/aliases/{alias_id}", response_model=Message)
def delete_alias(alias_id: int, db: Session = Depends(get_db)):
    alias = db.query(InstrumentAlias).filter(InstrumentAlias.id == alias_id).first()
    if not alias:
        raise HTTPException(404, "Alias not found")
    db.delete(alias)
    db.commit()
    return Message(message="Alias deleted")


@router.post("/instruments/{instrument_id}/services", response_model=ServiceRead)
def create_service(instrument_id: int, payload: ServiceCreate, db: Session = Depends(get_db)):
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(404, "Instrument not found")
    service = InstrumentService(instrument_id=instrument_id, **payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/services/{service_id}", response_model=ServiceRead)
def update_service(service_id: int, payload: ServiceCreate, db: Session = Depends(get_db)):
    service = db.query(InstrumentService).filter(InstrumentService.id == service_id).first()
    if not service:
        raise HTTPException(404, "Service not found")
    for k, v in payload.model_dump().items():
        setattr(service, k, v)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/services/{service_id}", response_model=Message)
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(InstrumentService).filter(InstrumentService.id == service_id).first()
    if not service:
        raise HTTPException(404, "Service not found")
    db.delete(service)
    db.commit()
    return Message(message="Service deleted")
