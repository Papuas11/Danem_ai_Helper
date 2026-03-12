import re


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def extract_quantity(value: str) -> int | None:
    match = re.search(r"\b(\d{1,4})\b", value)
    return int(match.group(1)) if match else None
