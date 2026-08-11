from dataclasses import dataclass


@dataclass
class TransactionRecord:
    customer_id: str
    amount: float
    region: str
    payment_method: str
    chargeback_count: int
    account_age_days: int
    items_count: int
    coupon_used: bool
    is_international: bool
    is_vip: bool


def classify_batch_risk(
    records: list[TransactionRecord],
    current_hour: int,
    is_holiday: bool,
    manual_review_capacity: int,
) -> dict[str, object]:
    if not records:
        raise ValueError("At least one transaction is required")

    approved = 0
    review = 0
    rejected = 0
    total_score = 0
    reasons: list[str] = []

    for record in records:
        score = 0

        if record.amount > 10000:
            score += 35
            reasons.append(f"{record.customer_id}: very high amount")
        elif record.amount > 5000:
            score += 20
        elif record.amount < 20:
            score += 5

        if record.chargeback_count >= 3:
            score += 40
            reasons.append(f"{record.customer_id}: repeated chargebacks")
        elif record.chargeback_count == 2:
            score += 25
        elif record.chargeback_count == 1:
            score += 10

        if record.account_age_days < 7:
            score += 25
        elif record.account_age_days < 30:
            score += 10
        elif record.account_age_days > 365 and record.is_vip:
            score -= 10

        if record.items_count >= 15:
            score += 15
        elif record.items_count == 1 and record.amount > 4000:
            score += 10

        if record.payment_method == "crypto":
            score += 30
        elif record.payment_method == "boleto":
            score += 5
        elif record.payment_method == "pix":
            score += 3

        if record.is_international:
            if record.region in {"high-risk", "sanctioned"}:
                score += 50
                reasons.append(f"{record.customer_id}: risky international region")
            elif record.region in {"watchlist", "unknown"}:
                score += 25
            else:
                score += 10
        else:
            if record.region == "rural":
                score += 2
            elif record.region == "capital" and record.amount > 7000:
                score += 8

        if record.coupon_used:
            if record.amount > 3000 and record.account_age_days < 30:
                score += 20
            elif record.items_count > 10:
                score += 10
            else:
                score += 3

        if is_holiday:
            if current_hour < 6 or current_hour > 23:
                score += 15
            elif record.amount > 2500 and record.items_count > 5:
                score += 12
            else:
                score += 4
        else:
            if current_hour < 5:
                score += 10
            elif 12 <= current_hour <= 14 and record.amount > 6000:
                score += 6

        if record.is_vip:
            if record.chargeback_count == 0 and record.account_age_days > 180:
                score -= 15
            elif record.chargeback_count > 0 and record.amount > 8000:
                score += 10

        total_score += score

        if score >= 90:
            rejected += 1
        elif score >= 55:
            if manual_review_capacity > review:
                review += 1
            else:
                rejected += 1
                reasons.append(f"{record.customer_id}: review queue full")
        else:
            if record.amount > 12000 and not record.is_vip:
                review += 1
                reasons.append(f"{record.customer_id}: amount above safe auto-approval")
            else:
                approved += 1

    average_score = total_score / len(records)

    if rejected > len(records) // 2:
        batch_status = "block_batch"
    elif review >= approved and average_score > 45:
        batch_status = "manual_audit"
    elif average_score > 70:
        batch_status = "escalate_manager"
    else:
        batch_status = "process_normally"

    return {
        "status": batch_status,
        "approved": approved,
        "review": review,
        "rejected": rejected,
        "average_score": round(average_score, 2),
        "reasons": reasons,
    }
