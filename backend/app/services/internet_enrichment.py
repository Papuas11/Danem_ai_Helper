from app.core.config import settings


class InternetEnrichmentService:
    """Scaffold for future enrichment; never mutates instrument DB in MVP."""

    def __init__(self) -> None:
        self.mode = settings.internet_enrichment_mode

    def enrich(self, query: str) -> dict:
        if self.mode == "OFF":
            return {"enabled": False, "mode": self.mode, "results": [], "note": "Internet enrichment disabled"}
        if self.mode == "WHITELIST":
            return {"enabled": True, "mode": self.mode, "results": [], "note": "Whitelist enrichment scaffold"}
        return {"enabled": True, "mode": self.mode, "results": [], "note": "Full enrichment scaffold"}
