import json


def dumps_list(value: list[str] | None) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def loads_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []
