from app.risk_rules import TransactionRecord


def _score_amount(record: TransactionRecord, reasons: list[str]) -> int:
    if record.amount > 10000:
        reasons.append(f"{record.customer_id}: very high amount")
        return 35
    if record.amount > 5000:
        return 20
    if record.amount < 20:
        return 5
    return 0


def _score_chargebacks(record: TransactionRecord, reasons: list[str]) -> int:
    if record.chargeback_count >= 3:
        reasons.append(f"{record.customer_id}: repeated chargebacks")
        return 40
    if record.chargeback_count == 2:
        return 25
    if record.chargeback_count == 1:
        return 10
    return 0


def _score_account_age(record: TransactionRecord) -> int:
    if record.account_age_days < 7:
        return 25
    if record.account_age_days < 30:
        return 10
    if record.account_age_days > 365 and record.is_vip:
        return -10
    return 0


def _score_items(record: TransactionRecord) -> int:
    if record.items_count >= 15:
        return 15
    if record.items_count == 1 and record.amount > 4000:
        return 10
    return 0


def _score_payment_method(record: TransactionRecord) -> int:
    payment_scores = {
        "crypto": 30,
        "boleto": 5,
        "pix": 3,
    }
    return payment_scores.get(record.payment_method, 0)


def _score_region(record: TransactionRecord, reasons: list[str]) -> int:
    if record.is_international:
        if record.region in {"high-risk", "sanctioned"}:
            reasons.append(f"{record.customer_id}: risky international region")
            return 50
        if record.region in {"watchlist", "unknown"}:
            return 25
        return 10

    if record.region == "rural":
        return 2
    if record.region == "capital" and record.amount > 7000:
        return 8
    return 0


def _score_coupon(record: TransactionRecord) -> int:
    if not record.coupon_used:
        return 0
    if record.amount > 3000 and record.account_age_days < 30:
        return 20
    if record.items_count > 10:
        return 10
    return 3


def _score_timing(
    record: TransactionRecord,
    current_hour: int,
    is_holiday: bool,
) -> int:
    if is_holiday:
        if current_hour < 6 or current_hour > 23:
            return 15
        if record.amount > 2500 and record.items_count > 5:
            return 12
        return 4

    if current_hour < 5:
        return 10
    if 12 <= current_hour <= 14 and record.amount > 6000:
        return 6
    return 0


def _score_vip_adjustment(record: TransactionRecord) -> int:
    if not record.is_vip:
        return 0
    if record.chargeback_count == 0 and record.account_age_days > 180:
        return -15
    if record.chargeback_count > 0 and record.amount > 8000:
        return 10
    return 0


def _classify_record(
    record: TransactionRecord,
    score: int,
    review_count: int,
    manual_review_capacity: int,
    reasons: list[str],
) -> str:
    if score >= 90:
        return "rejected"

    if score >= 55:
        if manual_review_capacity > review_count:
            return "review"
        reasons.append(f"{record.customer_id}: review queue full")
        return "rejected"

    if record.amount > 12000 and not record.is_vip:
        reasons.append(f"{record.customer_id}: amount above safe auto-approval")
        return "review"

    return "approved"


def _batch_status(
    approved: int,
    review: int,
    rejected: int,
    average_score: float,
    total_records: int,
) -> str:
    if rejected > total_records // 2:
        return "block_batch"
    if review >= approved and average_score > 45:
        return "manual_audit"
    if average_score > 70:
        return "escalate_manager"
    return "process_normally"


def classify_batch_risk_refactored(
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
        score = sum(
            [
                _score_amount(record, reasons),
                _score_chargebacks(record, reasons),
                _score_account_age(record),
                _score_items(record),
                _score_payment_method(record),
                _score_region(record, reasons),
                _score_coupon(record),
                _score_timing(record, current_hour, is_holiday),
                _score_vip_adjustment(record),
            ]
        )

        total_score += score
        decision = _classify_record(
            record,
            score,
            review,
            manual_review_capacity,
            reasons,
        )

        if decision == "approved":
            approved += 1
        elif decision == "review":
            review += 1
        else:
            rejected += 1

    average_score = total_score / len(records)
    batch_status = _batch_status(
        approved,
        review,
        rejected,
        average_score,
        len(records),
    )

    return {
        "status": batch_status,
        "approved": approved,
        "review": review,
        "rejected": rejected,
        "average_score": round(average_score, 2),
        "reasons": reasons,
    }
