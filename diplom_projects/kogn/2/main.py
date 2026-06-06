from typing import Any


def filter_and_transform(data: list[dict[str, Any]], min_score: int) -> list[str]:
    result = []
    for item in data:
        if item.get("score", 0) >= min_score:
            name = item.get("name", "").upper()
            result.append(name)
    return result
