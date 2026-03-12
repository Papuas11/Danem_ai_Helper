from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.models.instrument import Instrument, InstrumentAlias, InstrumentService
from app.schemas.instrument import (
    AliasCreate,
    InstrumentCreate,
    InstrumentRead,
    InstrumentUpdate,
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
)
from app.utils.json import dumps_list, loads_list
from app.utils.text import normalize_text

router = APIRouter(prefix="/api", tags=["instruments"])


def _service_read(service: InstrumentService) -> ServiceRead:
    return ServiceRead(
        id=service.id,
        instrument_id=service.instrument_id,
        service_type=service.service_type,
        unit_type=service.unit_type,
        base_price=service.base_price,
        base_cost=service.base_cost,
        turnaround_days=service.turnaround_days,
        turnaround_hours=service.turnaround_hours,
        onsite_available=service.onsite_available,
        onsite_price=service.onsite_price,
        onsite_cost=service.onsite_cost,
        required_client_data=loads_list(service.required_client_data),
        issued_documents=loads_list(service.issued_documents),
        status=service.status,
        service_comment=service.service_comment,
        created_at=service.created_at,
        updated_at=service.updated_at,
    )


def _instrument_read(inst: Instrument) -> InstrumentRead:
    return InstrumentRead(
        id=inst.id,
        name=inst.name,
        category=inst.category,
        status=inst.status,
        manager_comment=inst.manager_comment,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
        aliases=list(inst.aliases),
        services=[_service_read(s) for s in inst.services],
    )


@router.get("/instruments", response_model=list[InstrumentRead])
def list_instruments(db: Session = Depends(get_db)):
    rows = db.query(Instrument).options(selectinload(Instrument.aliases), selectinload(Instrument.services)).all()
    return [_instrument_read(r) for r in rows]


@router.post("/instruments", response_model=InstrumentRead)
def create_instrument(payload: InstrumentCreate, db: Session = Depends(get_db)):
    inst = Instrument(**payload.model_dump())
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return _instrument_read(inst)


@router.get("/instruments/{instrument_id}", response_model=InstrumentRead)
def get_instrument(instrument_id: int, db: Session = Depends(get_db)):
    inst = db.query(Instrument).options(selectinload(Instrument.aliases), selectinload(Instrument.services)).filter(Instrument.id == instrument_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return _instrument_read(inst)


@router.put("/instruments/{instrument_id}", response_model=InstrumentRead)
def update_instrument(instrument_id: int, payload: InstrumentUpdate, db: Session = Depends(get_db)):
    inst = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(inst, k, v)
    db.commit()
    db.refresh(inst)
    return _instrument_read(inst)


@router.delete("/instruments/{instrument_id}")
def delete_instrument(instrument_id: int, db: Session = Depends(get_db)):
    inst = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    inst.status = "archived"
    db.commit()
    return {"ok": True}


@router.post("/instruments/{instrument_id}/aliases")
def create_alias(instrument_id: int, payload: AliasCreate, db: Session = Depends(get_db)):
    inst = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    alias = InstrumentAlias(instrument_id=instrument_id, alias=payload.alias, normalized_alias=normalize_text(payload.alias))
    db.add(alias)
    db.commit()
    db.refresh(alias)
    return alias


@router.delete("/aliases/{alias_id}")
def delete_alias(alias_id: int, db: Session = Depends(get_db)):
    alias = db.query(InstrumentAlias).filter(InstrumentAlias.id == alias_id).first()
    if not alias:
        raise HTTPException(status_code=404, detail="Alias not found")
    db.delete(alias)
    db.commit()
    return {"ok": True}


@router.post("/instruments/{instrument_id}/services", response_model=ServiceRead)
def create_service(instrument_id: int, payload: ServiceCreate, db: Session = Depends(get_db)):
    service = InstrumentService(
        instrument_id=instrument_id,
        service_type=payload.service_type,
        unit_type=payload.unit_type,
        base_price=payload.base_price,
        base_cost=payload.base_cost,
        turnaround_days=payload.turnaround_days,
        turnaround_hours=payload.turnaround_hours,
        onsite_available=payload.onsite_available,
        onsite_price=payload.onsite_price,
        onsite_cost=payload.onsite_cost,
        required_client_data=dumps_list(payload.required_client_data),
        issued_documents=dumps_list(payload.issued_documents),
        status=payload.status,
        service_comment=payload.service_comment,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return _service_read(service)


@router.put("/services/{service_id}", response_model=ServiceRead)
def update_service(service_id: int, payload: ServiceUpdate, db: Session = Depends(get_db)):
    service = db.query(InstrumentService).filter(InstrumentService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    data = payload.model_dump()
    for k, v in data.items():
        if k in {"required_client_data", "issued_documents"}:
            setattr(service, k, dumps_list(v))
        else:
            setattr(service, k, v)
    db.commit()
    db.refresh(service)
    return _service_read(service)


@router.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(InstrumentService).filter(InstrumentService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    db.delete(service)
    db.commit()
    return {"ok": True}
