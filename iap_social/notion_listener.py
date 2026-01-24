#!/usr/bin/env python3
"""
Notion API listener: poll a "Post Queue" database for pending rows,
auto-create posts (generate + optional Mastodon publish), update Notion status.

Setup:
1. Create a Notion database with:
   - Name (title)
   - Platform (select): twitter | linkedin | instagram | facebook
   - Type (select): general | product | technology | use_case | announcement | educational
   - Topic (text, optional)
   - Status (select): Pending | Generated | Posted
2. Share the DB with your integration. Set NOTION_POST_QUEUE_DATABASE_ID in .env.
3. Run: python notion_listener.py [--post-mastodon] [--interval 60]
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_POST_QUEUE_DATABASE_ID = os.getenv("NOTION_POST_QUEUE_DATABASE_ID")


def _prop_text(props: dict, name: str) -> str:
    p = props.get(name, {})
    if p.get("type") != "rich_text" or not p.get("rich_text"):
        return ""
    return "".join(t.get("plain_text", "") for t in p["rich_text"]).strip()


def _prop_select(props: dict, name: str) -> str:
    p = props.get(name, {})
    if p.get("type") != "select" or not p.get("select"):
        return ""
    return (p["select"].get("name") or "").strip().lower()


def _prop_title(props: dict, name: str = "Name") -> str:
    p = props.get(name, {})
    if p.get("type") != "title" or not p.get("title"):
        return ""
    return "".join(t.get("plain_text", "") for t in p["title"]).strip()


def fetch_pending_queue(notion, database_id: str) -> list[dict]:
    """Fetch rows with Status = Pending."""
    db_id = database_id.replace("-", "").strip()
    try:
        # Filter for Status = Pending (match select name)
        resp = notion.databases.query(
            database_id=db_id,
            filter={
                "property": "Status",
                "select": {"equals": "Pending"},
            },
        )
    except Exception as e:
        print(f"[notion_listener] DB query failed: {e}")
        return []
    out = []
    for page in resp.get("results", []):
        pid = page["id"]
        props = page.get("properties", {})
        platform = _prop_select(props, "Platform") or "twitter"
        ptype = _prop_select(props, "Type") or "general"
        topic = _prop_text(props, "Topic")
        name = _prop_title(props)
        out.append({
            "page_id": pid,
            "name": name,
            "platform": platform,
            "post_type": ptype,
            "topic": topic or None,
        })
    return out


def update_page_status(notion, page_id: str, status: str) -> bool:
    """Update Status of a Notion page."""
    try:
        notion.pages.update(
            page_id=page_id,
            properties={"Status": {"select": {"name": status}}},
        )
        return True
    except Exception as e:
        print(f"[notion_listener] Update failed for {page_id}: {e}")
        return False


def process_one(notion, item: dict, post_to_mastodon: bool) -> bool:
    """Generate post, optionally post to Mastodon, update Notion."""
    from database import insert_post, mark_posted, get_post
    from rag import get_create_post_context
    from generate_social_posts import generate_social_post
    from openai import OpenAI
    from notion_docs import fetch_docs_from_notion

    platform = item["platform"]
    post_type = item["post_type"]
    topic = item["topic"]
    page_id = item["page_id"]

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[notion_listener] OPENROUTER_API_KEY not set")
        return False

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    doc_content = get_create_post_context(platform, post_type, topic, top_k=5, max_chars=4000)
    if not doc_content:
        try:
            doc_content = fetch_docs_from_notion()
        except Exception:
            doc_content = "Widvid is an AI video generation platform."

    content = generate_social_post(client, doc_content, platform=platform, post_type=post_type, topic=topic)
    if not content:
        content = "Widvid: AI video generation. Try it! #AIVideo #Widvid"

    post = insert_post(platform=platform, content=content, post_type=post_type, topic=topic)
    post_id = post["id"]

    update_page_status(notion, page_id, "Generated")

    if post_to_mastodon:
        try:
            from post_to_mastodon import post_to_mastodon, MASTODON_INSTANCE, MASTODON_ACCESS_TOKEN
            if MASTODON_ACCESS_TOKEN:
                res = post_to_mastodon(content, MASTODON_INSTANCE, MASTODON_ACCESS_TOKEN, image_path_or_url=None)
                if res.get("success"):
                    mark_posted(
                        post_id,
                        mastodon_url=res.get("url") or "",
                        mastodon_id=str(res.get("id", "")),
                        mastodon_created_at=res.get("created_at") or "",
                    )
                    update_page_status(notion, page_id, "Posted")
                    print(f"[notion_listener] Posted to Mastodon: {res.get('url')}")
        except Exception as e:
            print(f"[notion_listener] Mastodon post failed: {e}")

    print(f"[notion_listener] Processed page {page_id} -> post id {post_id}")
    return True


def run_once(post_to_mastodon: bool) -> int:
    """Process all pending Notion queue items. Returns count processed."""
    if not NOTION_TOKEN or not NOTION_POST_QUEUE_DATABASE_ID:
        print("[notion_listener] Set NOTION_TOKEN and NOTION_POST_QUEUE_DATABASE_ID")
        return 0

    from notion_client import Client
    notion = Client(auth=NOTION_TOKEN)
    pending = fetch_pending_queue(notion, NOTION_POST_QUEUE_DATABASE_ID)
    n = 0
    for item in pending:
        try:
            if process_one(notion, item, post_to_mastodon):
                n += 1
        except Exception as e:
            print(f"[notion_listener] Error processing {item.get('page_id')}: {e}")
    return n


def main():
    ap = argparse.ArgumentParser(description="Notion Post Queue listener – auto-create posts")
    ap.add_argument("--post-mastodon", action="store_true", help="Also post to Mastodon")
    ap.add_argument("--interval", type=int, default=0, help="Poll interval seconds (0 = run once)")
    args = ap.parse_args()

    if not NOTION_TOKEN:
        print("NOTION_TOKEN not set")
        sys.exit(1)
    if not NOTION_POST_QUEUE_DATABASE_ID:
        print("NOTION_POST_QUEUE_DATABASE_ID not set. Create a Post Queue DB and share with integration.")
        sys.exit(1)

    if args.interval <= 0:
        run_once(args.post_mastodon)
        return

    print(f"[notion_listener] Polling every {args.interval}s (--post-mastodon={args.post_mastodon})")
    while True:
        try:
            n = run_once(args.post_mastodon)
            if n:
                print(f"[notion_listener] Processed {n} items")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[notion_listener] Poll error: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
