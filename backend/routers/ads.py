# ═══════════════════════════════════════════
# Ads Router — Impression Tracking
# ═══════════════════════════════════════════

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from middleware.auth import get_current_user_id
from models.schemas import AdImpressionCreate

router = APIRouter()

# In-memory ad impression store
ad_impressions: list[dict] = []


@router.post("/impression")
async def log_impression(
    data: AdImpressionCreate,
    user_id: str = Depends(get_current_user_id),
):
    impression = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "ad_type": data.ad_type,
        "ad_brand": data.ad_brand,
        "clicked": data.clicked,
        "created_at": datetime.now(timezone.utc),
    }
    ad_impressions.append(impression)

    return {"message": "Impression logged", "id": impression["id"]}


@router.get("/stats")
async def get_ad_stats(user_id: str = Depends(get_current_user_id)):
    """Get ad impression stats (for admin/demo)."""
    total = len(ad_impressions)
    clicks = sum(1 for a in ad_impressions if a["clicked"])
    by_type = {}
    for a in ad_impressions:
        t = a["ad_type"]
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "total_impressions": total,
        "total_clicks": clicks,
        "ctr": round(clicks / total * 100, 2) if total > 0 else 0,
        "by_type": by_type,
    }
