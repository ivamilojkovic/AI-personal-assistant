"""
Subscription detection LangGraph workflow.

Nodes:
  fetch_email_ids   → fetch_metadata → classify → filter_new → categorize → save_and_return
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from email_assistant.core.logger import Logger
from email_assistant.core.prompts import SUBSCRIPTION_CLASSIFICATION_PROMPT
from email_assistant.core.schemas import SubscriptionScanState
from email_assistant.services.subscription_service import SubscriptionService

load_dotenv()

logger = Logger.get_logger(__name__)

# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _parse_email_ids_from_result(result: Any) -> list[str]:
    """Extract message IDs from MCP search_emails tool result."""
    text = result.content[0].text if hasattr(result, "content") else str(result)
    ids = []
    for line in text.split("\n"):
        if line.strip().startswith("Message ID:"):
            ids.append(line.split("Message ID:")[1].strip())
    return ids


def _get_subscriptions_filepath() -> str:
    return os.getenv("SUBSCRIPTIONS_FILE", "subscriptions.json")


# ------------------------------------------------------------------ #
# Nodes                                                                #
# ------------------------------------------------------------------ #

async def fetch_email_ids_node(state: SubscriptionScanState) -> dict:
    """Fetch email IDs for the given date range."""
    logger.info("Subscription graph: fetch_email_ids")
    try:
        after_str = state.after_date.strftime("%Y/%m/%d")
        async with state.mcp as client:
            result = await client.call_tool(
                "search_emails",
                {"after_date": after_str, "max_results": state.max_results},
            )
        ids = _parse_email_ids_from_result(result)
        logger.info(f"Fetched {len(ids)} email IDs")
        return {"email_ids": ids}
    except Exception as e:
        logger.error(f"fetch_email_ids failed: {e}", exc_info=True)
        return {"email_ids": [], "status": "error", "error": str(e)}


async def fetch_metadata_node(state: SubscriptionScanState) -> dict:
    """Fetch From, Subject, Date and unsubscribe headers for each email ID."""
    logger.info("Subscription graph: fetch_metadata")
    if not state.email_ids:
        return {"metadata": []}
    try:
        async with state.mcp as client:
            result = await client.call_tool(
                "get_email_metadata",
                {"message_ids": state.email_ids},
            )
        # FastMCP serializes list[dict] as one TextContent item per dict.
        # Collect all content items and normalise to list[dict].
        if hasattr(result, "content"):
            metadata = []
            for item in result.content:
                raw = item.text if hasattr(item, "text") else str(item)
                try:
                    parsed = json.loads(raw)
                except Exception:
                    continue
                if isinstance(parsed, list):
                    metadata.extend(parsed)
                elif isinstance(parsed, dict):
                    metadata.append(parsed)
        else:
            metadata = result if isinstance(result, list) else json.loads(str(result))

        logger.info(f"Fetched metadata for {len(metadata)} emails")
        return {"metadata": metadata}
    except Exception as e:
        logger.error(f"fetch_metadata failed: {e}", exc_info=True)
        return {"metadata": [], "status": "error", "error": str(e)}


async def classify_node(state: SubscriptionScanState) -> dict:
    """Use LLM to classify emails as subscriptions using only From + Subject."""
    logger.info("Subscription graph: classify")
    if not state.metadata:
        return {"metadata": []}

    llm = init_chat_model(
        model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        temperature=0,
    )

    # Build a single batch prompt listing all emails
    lines = []
    for i, m in enumerate(state.metadata):
        if "error" in m:
            continue
        lines.append(f"{i}. From: {m.get('from', '')} | Subject: {m.get('subject', '')}")

    if not lines:
        return {"metadata": []}

    batch_prompt = (
        "Classify each email below as a newsletter/subscription or not.\n"
        "For each item return a JSON object on its own line with keys: "
        "index (int), is_subscription (bool), confidence (0-100), name (string).\n"
        "Use ONLY the From address and Subject. Output one JSON object per line, nothing else.\n\n"
        + "\n".join(lines)
    )

    try:
        response = await llm.ainvoke([HumanMessage(content=batch_prompt)])
        response_text = response.content.strip()

        # Parse one JSON per line
        classifications: dict[int, dict] = {}
        for line in response_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                classifications[obj["index"]] = obj
            except Exception:
                pass

        # Annotate metadata with classification results
        annotated = []
        for i, m in enumerate(state.metadata):
            if "error" in m:
                continue
            cls = classifications.get(i, {})
            m["is_subscription"] = cls.get("is_subscription", False)
            m["confidence"] = cls.get("confidence", 0)
            m["sender_name"] = cls.get("name", m.get("from", ""))
            annotated.append(m)

        logger.info(f"Classified {len(annotated)} emails")
        return {"metadata": annotated}
    except Exception as e:
        logger.error(f"classify failed: {e}", exc_info=True)
        return {"metadata": state.metadata, "status": "error", "error": str(e)}


def filter_new_node(state: SubscriptionScanState) -> dict:
    """Keep only emails classified as subscriptions and not already tracked."""
    logger.info("Subscription graph: filter_new")
    service = SubscriptionService(_get_subscriptions_filepath())
    existing = {s["sender_email"].lower() for s in service.get_all()}

    candidates = []
    for m in state.metadata:
        if not m.get("is_subscription"):
            continue
        # Extract bare email address from "Name <email>" format
        from_raw = m.get("from", "")
        import re
        match = re.search(r"<([^>]+)>", from_raw)
        sender_email = match.group(1).strip() if match else from_raw.strip()
        if sender_email.lower() not in existing:
            m["sender_email"] = sender_email
            candidates.append(m)

    logger.info(f"{len(candidates)} new subscriptions found")
    return {"new_subscriptions": candidates}


def categorize_node(state: SubscriptionScanState) -> dict:
    """Determine unsubscribe_path (auto/manual) for each new subscription."""
    logger.info("Subscription graph: categorize")
    service = SubscriptionService(_get_subscriptions_filepath())

    for m in state.new_subscriptions:
        path, url = service.parse_unsubscribe_header(
            m.get("list_unsubscribe", ""),
            m.get("list_unsubscribe_post", ""),
        )
        m["unsubscribe_path"] = path
        m["unsubscribe_url"] = url
        m["one_click"] = service.is_one_click(m.get("list_unsubscribe_post", ""))

    return {"new_subscriptions": state.new_subscriptions}


def save_and_return_node(state: SubscriptionScanState) -> dict:
    """Persist new subscriptions to JSON and return final status."""
    logger.info("Subscription graph: save_and_return")
    service = SubscriptionService(_get_subscriptions_filepath())

    added = 0
    for m in state.new_subscriptions:
        record = {
            "sender_name": m.get("sender_name", m.get("sender_email", "")),
            "last_received": m.get("date", datetime.now(timezone.utc).isoformat()),
            "unsubscribe_path": m.get("unsubscribe_path", "manual"),
            "unsubscribe_url": m.get("unsubscribe_url", ""),
            "one_click": m.get("one_click", False),
            "confidence": m.get("confidence", 0),
            "message_id": m.get("id", ""),
        }
        if service.upsert(m["sender_email"], record):
            added += 1

    service.update_last_poll()
    logger.info(f"Saved {added} new subscriptions")
    return {"status": "completed", "new_subscriptions": state.new_subscriptions}


# ------------------------------------------------------------------ #
# Graph factory                                                        #
# ------------------------------------------------------------------ #

def create_subscription_graph():
    workflow = StateGraph(SubscriptionScanState)

    workflow.add_node("fetch_email_ids", fetch_email_ids_node)
    workflow.add_node("fetch_metadata", fetch_metadata_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("filter_new", filter_new_node)
    workflow.add_node("categorize", categorize_node)
    workflow.add_node("save_and_return", save_and_return_node)

    workflow.set_entry_point("fetch_email_ids")
    workflow.add_edge("fetch_email_ids", "fetch_metadata")
    workflow.add_edge("fetch_metadata", "classify")
    workflow.add_edge("classify", "filter_new")
    workflow.add_edge("filter_new", "categorize")
    workflow.add_edge("categorize", "save_and_return")
    workflow.add_edge("save_and_return", END)

    return workflow.compile()
