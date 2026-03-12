import re


def normalize_text(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered
