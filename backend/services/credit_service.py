# ═══════════════════════════════════════════
# Credit Service — Business Logic
# ═══════════════════════════════════════════

from datetime import datetime, timedelta, timezone
from typing import Optional

INITIAL_CREDITS = 10
DAILY_CREDIT_RESET = 10
AD_REFILL_AMOUNT = 5

# Credit costs per tool
TOOL_COSTS = {
    "remove-bg": 1,
    "remove-object": 1,
    "super-resolution": 2,
    "product-photo": 1,
    "replace-bg": 1,
    "text-to-image": 1,
    "uncrop": 2,
    "remove-text": 1,
}

# Transaction log (in-memory)
transactions: list[dict] = []


def get_tool_cost(tool_id: str) -> int:
    return TOOL_COSTS.get(tool_id, 1)


def check_and_reset_daily_credits(user: dict) -> bool:
    """Check if 24h have passed since last reset; if so, reset credits."""
    last_reset = user.get("last_credit_reset")
    if not last_reset:
        return False

    now = datetime.now(timezone.utc)
    if now - last_reset > timedelta(hours=24):
        user["credits"] = DAILY_CREDIT_RESET
        user["last_credit_reset"] = now
        log_transaction(user["id"], DAILY_CREDIT_RESET, "DAILY_RESET", "Daily credit reset")
        return True
    return False


def deduct_credits(user: dict, tool_id: str) -> tuple[bool, int]:
    """
    Attempt to deduct credits for a tool.
    Returns (success, remaining_credits).
    """
    # Check for daily reset first
    check_and_reset_daily_credits(user)

    cost = get_tool_cost(tool_id)
    if user["credits"] < cost:
        return False, user["credits"]

    user["credits"] -= cost
    log_transaction(user["id"], -cost, "DEDUCTION", f"Used {tool_id}")
    return True, user["credits"]


def refill_credits(user: dict) -> int:
    """Add credits from watching an ad."""
    user["credits"] += AD_REFILL_AMOUNT
    log_transaction(user["id"], AD_REFILL_AMOUNT, "AD_REFILL", "Watched video ad")
    return user["credits"]


def log_transaction(user_id: str, amount: int, tx_type: str, detail: Optional[str] = None):
    transactions.append({
        "user_id": user_id,
        "amount": amount,
        "type": tx_type,
        "detail": detail,
        "created_at": datetime.now(timezone.utc),
    })
