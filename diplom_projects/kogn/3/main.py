def aggregate_by_category(
    records: list[dict],
    categories: dict[str, list[str]],
    min_value: float
) -> dict[str, float]:
    totals = {cat: 0.0 for cat in categories}
    for cat, keywords in categories.items():             
        total = 0.0
        for rec in records:                            
            if rec.get("value", 0.0) > min_value and rec.get("category") in keywords:
                total += rec["value"]
        totals[cat] = total
    return totals