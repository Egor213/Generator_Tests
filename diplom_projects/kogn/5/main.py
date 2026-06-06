def process_transactions_heavy(
    transactions: list[dict],
    thresholds: dict[str, float],
    allowed_statuses: list[str],
    tag_weights: dict[str, float] | None = None
) -> dict[str, float]:
    if tag_weights is None:
        tag_weights = {}

    result = {}
    for tx in transactions:
        tx_type = tx.get("type", "default")
        threshold = thresholds.get(tx_type, 0.0)
        amount = tx.get("amount", 0.0)
        if amount > threshold:
            currency = tx.get("currency", "USD")
            if currency == "EUR":
                amount = amount * 1.1
                if tx.get("status") in allowed_statuses:
                    tags = tx.get("tags", [])
                    for tag in tags:
                        multiplier = tag_weights.get(tag, 1.0)
                        contrib = amount * multiplier
                        result[tag] = result.get(tag, 0.0) + contrib
    return result
