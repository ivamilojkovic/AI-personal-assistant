"""
Subscription Service — manages subscription detection state and unsubscribe execution.
"""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from email_assistant.core.logger import Logger

logger = Logger.get_logger(__name__)


class SubscriptionService:
    """Manages subscription JSON persistence and unsubscribe execution."""

    def __init__(self, filepath: str = "subscriptions.json"):
        self.filepath = Path(filepath)

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    def load(self) -> dict:
        if self.filepath.exists():
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {"last_poll": None, "subscriptions": []}

    def save(self, data: dict) -> None:
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def get_last_poll(self) -> Optional[datetime]:
        data = self.load()
        raw = data.get("last_poll")
        if raw:
            return datetime.fromisoformat(raw)
        return None

    def update_last_poll(self, dt: Optional[datetime] = None) -> None:
        data = self.load()
        data["last_poll"] = (dt or datetime.now(timezone.utc)).isoformat()
        self.save(data)

    def get_all(self) -> list:
        return self.load().get("subscriptions", [])

    def upsert(self, sender_email: str, new_data: dict) -> bool:
        """Add new subscription or update last_received if sender already tracked.

        Returns True if a new subscription was added, False if only updated.
        """
        data = self.load()
        subs = data["subscriptions"]

        for sub in subs:
            if sub["sender_email"].lower() == sender_email.lower():
                sub["last_received"] = new_data.get("last_received", sub["last_received"])
                if new_data.get("message_id"):
                    sub["message_id"] = new_data["message_id"]
                self.save(data)
                return False

        new_data["id"] = str(uuid.uuid4())
        new_data["sender_email"] = sender_email
        new_data.setdefault("first_detected", datetime.now(timezone.utc).isoformat())
        new_data.setdefault("status", "pending")
        new_data.setdefault("unsubscribed_at", None)
        new_data.setdefault("message_id", "")
        subs.append(new_data)
        self.save(data)
        return True

    def set_status(self, sub_id: str, status: str) -> Optional[dict]:
        data = self.load()
        for sub in data["subscriptions"]:
            if sub["id"] == sub_id:
                sub["status"] = status
                if status == "unsubscribed":
                    sub["unsubscribed_at"] = datetime.now(timezone.utc).isoformat()
                self.save(data)
                return sub
        return None

    def get_by_id(self, sub_id: str) -> Optional[dict]:
        for sub in self.get_all():
            if sub["id"] == sub_id:
                return sub
        return None

    # ------------------------------------------------------------------ #
    # Unsubscribe header parsing                                           #
    # ------------------------------------------------------------------ #

    def parse_unsubscribe_header(
        self, list_unsubscribe: str, list_unsubscribe_post: str = ""
    ) -> tuple[str, str]:
        """Parse List-Unsubscribe header value.

        Returns (path, url) where path is 'auto' or 'manual'.
        'auto' means there is an HTTPS URL we can POST to (user still clicks to confirm).
        """
        if not list_unsubscribe:
            return ("manual", "")

        https_urls = re.findall(r"<(https://[^>]+)>", list_unsubscribe, re.IGNORECASE)
        if https_urls:
            return ("auto", https_urls[0])

        return ("manual", "")

    def is_one_click(self, list_unsubscribe_post: str) -> bool:
        return "List-Unsubscribe=One-Click" in list_unsubscribe_post

    # ------------------------------------------------------------------ #
    # Unsubscribe execution (called only when user clicks [Unsubscribe])  #
    # ------------------------------------------------------------------ #

    async def execute_unsubscribe(self, url: str, one_click: bool) -> bool:
        """POST to the unsubscribe URL. Only called after user confirms in UI.

        Never opens browser, never sends email.
        For RFC 8058 one-click: POST with List-Unsubscribe=One-Click body.
        Otherwise: plain POST.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                if one_click:
                    response = await client.post(
                        url,
                        content="List-Unsubscribe=One-Click",
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                else:
                    # Non-RFC-8058: URL is a token-based landing page, use GET
                    response = await client.get(url)

            logger.info(f"Unsubscribe {'POST' if one_click else 'GET'} to {url} → HTTP {response.status_code}")
            return response.status_code < 400
        except Exception as e:
            logger.error(f"Unsubscribe POST failed for {url}: {e}")
            return False
