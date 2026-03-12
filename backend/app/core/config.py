from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "DANEM Sales Copilot API"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./danem_sales_copilot.db")
    internet_enrichment_mode: str = os.getenv("INTERNET_ENRICHMENT_MODE", "OFF")


settings = Settings()
