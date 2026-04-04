"""
REST API router for subscription management.
Mounted on the email-assistant FastAPI app at /subscriptions.
"""

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from email_assistant.agent.interface import EmailAssistant
from email_assistant.services.subscription_service import SubscriptionService
from email_assistant.core.logger import Logger

logger = Logger.get_logger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _service() -> SubscriptionService:
    return SubscriptionService(os.getenv("SUBSCRIPTIONS_FILE", "subscriptions.json"))


# ------------------------------------------------------------------ #
# Request / response models                                           #
# ------------------------------------------------------------------ #

class ScanRequest(BaseModel):
    days: int = 30


# ------------------------------------------------------------------ #
# Endpoints                                                           #
# ------------------------------------------------------------------ #

@router.get("")
async def get_subscriptions():
    """Return all tracked subscriptions."""
    return {"subscriptions": _service().get_all()}


@router.post("/scan")
async def scan_subscriptions(body: ScanRequest):
    """Trigger a full scan over the last N days and return newly detected subscriptions."""
    logger.info(f"Scan requested for last {body.days} days")
    after_date = datetime.now() - timedelta(days=body.days)

    agent = EmailAssistant()
    new_subs = await agent.scan_subscriptions(after_date=after_date)

    return {
        "new_count": len(new_subs),
        "new_subscriptions": new_subs,
        "all_subscriptions": _service().get_all(),
    }


@router.get("/poll")
async def poll_subscriptions():
    """Check for new subscription emails since the last poll. Updates last_poll timestamp."""
    logger.info("Poll requested")

    agent = EmailAssistant()
    new_subs = await agent.poll_subscriptions()

    return {
        "new_count": len(new_subs),
        "new_subscriptions": new_subs,
        "all_subscriptions": _service().get_all(),
    }


@router.post("/{sub_id}/unsubscribe")
async def unsubscribe(sub_id: str):
    """Execute unsubscribe for an auto-path subscription (user confirmed in UI).

    Returns 400 if the subscription requires manual unsubscription.
    """
    service = _service()
    sub = service.get_by_id(sub_id)

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub.get("unsubscribe_path") != "auto":
        raise HTTPException(
            status_code=400,
            detail="This subscription requires manual unsubscription in Gmail.",
        )

    url = sub.get("unsubscribe_url", "")
    if not url:
        raise HTTPException(status_code=400, detail="No unsubscribe URL available.")

    one_click = sub.get("one_click", False)
    success = await service.execute_unsubscribe(url, one_click)

    if not success:
        raise HTTPException(
            status_code=502,
            detail="Unsubscribe request failed. You may need to unsubscribe manually.",
        )

    updated = service.set_status(sub_id, "unsubscribed")

    # Best-effort: move all emails from this sender to Promotions category
    try:
        agent = EmailAssistant()
        await agent.categorize_emails_from_sender(sub["sender_email"])
    except Exception as e:
        logger.warning(f"Could not categorize emails for {sub.get('sender_email')}: {e}")

    return {"status": "unsubscribed", "subscription": updated}


@router.post("/{sub_id}/keep")
async def keep(sub_id: str):
    """Mark a subscription as kept (user chose to keep it)."""
    service = _service()
    sub = service.get_by_id(sub_id)

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    updated = service.set_status(sub_id, "kept")
    return {"status": "kept", "subscription": updated}
