"""
Fetch knowledge-base documentation from Notion via the API.
Replaces local WIDVID_OVERVIEW.md with Notion as the source of truth.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_KNOWLEDGE_PAGE_ID = os.getenv("NOTION_KNOWLEDGE_PAGE_ID") or os.getenv(
    "NOTION_PARENT_PAGE_ID"
)

# Block types that have rich_text we can extract
_RICH_TEXT_TYPES = (
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "quote",
    "callout",
    "toggle",
    "to_do",
)


def _plain_text_from_rich_text(rich_text: list[dict[str, Any]]) -> str:
    if not rich_text:
        return ""
    return "".join(item.get("plain_text", "") for item in rich_text)


def _text_from_block(block: dict[str, Any]) -> str:
    btype = block.get("type")
    if btype not in _RICH_TEXT_TYPES:
        return ""
    payload = block.get(btype)
    if not payload or "rich_text" not in payload:
        return ""
    return _plain_text_from_rich_text(payload["rich_text"])


def _fetch_blocks_recursive(notion: Any, block_id: str) -> list[str]:
    """Fetch all blocks under block_id (page or block) and return plain-text lines."""
    lines: list[str] = []
    cursor: str | None = None
    try:
        while True:
            kwargs: dict[str, Any] = {"block_id": block_id, "page_size": 100}
            if cursor:
                kwargs["start_cursor"] = cursor
            resp = notion.blocks.children.list(**kwargs)
            for block in resp.get("results", []):
                text = _text_from_block(block)
                if text:
                    lines.append(text)
                if block.get("has_children"):
                    nested = _fetch_blocks_recursive(notion, block["id"])
                    lines.extend(nested)
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")
            if not cursor:
                break
    except Exception:
        pass
    return lines


def fetch_docs_from_notion(page_id: str | None = None) -> str:
    """
    Fetch documentation from a Notion page and return plain text.
    Uses NOTION_KNOWLEDGE_PAGE_ID or NOTION_PARENT_PAGE_ID if page_id not given.
    """
    from notion_client import Client

    token = NOTION_TOKEN
    if not token:
        raise ValueError(
            "NOTION_TOKEN is not set. Add it to .env to use Notion as the knowledge base."
        )
    pid = page_id or NOTION_KNOWLEDGE_PAGE_ID
    if not pid:
        raise ValueError(
            "NOTION_KNOWLEDGE_PAGE_ID or NOTION_PARENT_PAGE_ID is not set. "
            "Add one to .env and share that Notion page with your integration."
        )
    # Normalize page ID: strip dashes, notion-client accepts both
    pid = pid.replace("-", "").strip()
    notion = Client(auth=token)
    lines = _fetch_blocks_recursive(notion, pid)
    return "\n\n".join(lines).strip()


def load_widvid_docs() -> str:
    """
    Load Widvid/docs content from Notion. Use this as the drop-in replacement
    for the former file-based load_widvid_docs.
    """
    return fetch_docs_from_notion()
