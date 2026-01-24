#!/usr/bin/env python3
"""
Mastodon comments listener: poll notifications for mentions,
auto-reply using AI (Widvid context). Tracks replied-to IDs to avoid duplicates.

Set MASTODON_ACCESS_TOKEN, MASTODON_INSTANCE, OPENROUTER_API_KEY in .env.
Run: python mastodon_listener.py [--interval 90]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
MASTODON_INSTANCE = os.getenv("MASTODON_INSTANCE", "https://mastodon.social")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def fetch_mentions(limit: int = 20) -> list[dict]:
    """Fetch mention-type notifications from Mastodon."""
    url = f"{MASTODON_INSTANCE.rstrip('/')}/api/v1/notifications"
    headers = {"Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"}
    params = {"types[]": "mention", "limit": limit}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[mastodon_listener] Notifications fetch failed: {e}")
        return []


def post_reply(status_id: str, reply_text: str) -> dict:
    """Post a reply to a Mastodon status."""
    url = f"{MASTODON_INSTANCE.rstrip('/')}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}", "Content-Type": "application/json"}
    if len(reply_text) > 500:
        reply_text = reply_text[:497] + "..."
    payload = {"status": reply_text, "in_reply_to_id": status_id, "visibility": "public"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        return {"success": True, "data": r.json()}
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def get_widvid_context() -> str:
    """Load Widvid docs for reply context (Notion or fallback)."""
    try:
        from notion_docs import fetch_docs_from_notion
        return fetch_docs_from_notion()
    except Exception:
        pass
    try:
        from rag import get_create_post_context
        ctx = get_create_post_context("twitter", "general", None, top_k=5, max_chars=4000)
        if ctx:
            return ctx
    except Exception:
        pass
    return "Widvid is an AI video generation platform using diffusion models."


def generate_reply(client: OpenAI, status_content: str, account_acct: str, widvid_docs: str) -> str | None:
    """Generate a single reply to a mention."""
    content_plain = re.sub(r"<[^>]+>", "", status_content or "").replace("&nbsp;", " ").strip()[:500]
    system = """You are a friendly social media manager for Widvid, an AI video generation platform.
Reply to Mastodon mentions helpfully and concisely. Be conversational, add value, mention Widvid when relevant.
Keep replies under 500 characters. Use emojis sparingly."""
    user = f"""Someone mentioned us on Mastodon. Reply to them.

Their post (@{account_acct}):
{content_plain}

Widvid context:
{widvid_docs[:4000]}

Write a single, engaging reply. No JSON, no prefixes – just the reply text."""

    try:
        resp = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.7,
            max_tokens=300,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text if text else None
    except Exception as e:
        print(f"[mastodon_listener] LLM error: {e}")
        return None


def process_mentions() -> int:
    """Process new mentions: generate reply, post, record. Returns count processed."""
    from database import mastodon_replied_ids, mastodon_replied_record, init_db

    init_db()
    replied = mastodon_replied_ids()

    if not MASTODON_ACCESS_TOKEN or not OPENROUTER_API_KEY:
        print("[mastodon_listener] MASTODON_ACCESS_TOKEN and OPENROUTER_API_KEY required")
        return 0

    notifications = fetch_mentions()
    widvid_docs = get_widvid_context()
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
    n = 0

    for notif in notifications:
        nid = str(notif.get("id", ""))
        if not nid or nid in replied:
            continue
        if notif.get("type") != "mention":
            continue
        status = notif.get("status")
        if not status:
            continue
        status_id = str(status.get("id", ""))
        if not status_id:
            continue
        account = notif.get("account", {})
        acct = account.get("acct", "unknown")
        content = status.get("content", "")

        reply_text = generate_reply(client, content, acct, widvid_docs)
        if not reply_text:
            continue

        result = post_reply(status_id, reply_text)
        if result.get("success"):
            mastodon_replied_record(nid, status_id)
            replied.add(nid)
            n += 1
            print(f"[mastodon_listener] Replied to mention {nid} (@{acct})")
        else:
            print(f"[mastodon_listener] Post reply failed: {result.get('error')}")

    return n


def main():
    ap = argparse.ArgumentParser(description="Mastodon mentions listener – auto-reply")
    ap.add_argument("--interval", type=int, default=0, help="Poll interval seconds (0 = run once)")
    args = ap.parse_args()

    if not MASTODON_ACCESS_TOKEN:
        print("MASTODON_ACCESS_TOKEN not set")
        sys.exit(1)
    if not OPENROUTER_API_KEY:
        print("OPENROUTER_API_KEY not set")
        sys.exit(1)

    if args.interval <= 0:
        process_mentions()
        return

    print(f"[mastodon_listener] Polling mentions every {args.interval}s")
    while True:
        try:
            n = process_mentions()
            if n:
                print(f"[mastodon_listener] Processed {n} mentions")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[mastodon_listener] Poll error: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
