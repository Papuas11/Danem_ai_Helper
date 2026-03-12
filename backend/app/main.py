from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.deals import router as deals_router
from app.api.instruments import router as instruments_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.db.seed import seed_data
from app import models  # noqa: F401

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(instruments_router)
app.include_router(deals_router)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}
