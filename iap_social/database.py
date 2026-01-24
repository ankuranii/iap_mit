"""
SQLite database for iap_social posts.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

DB_PATH = os.environ.get("IAP_SOCIAL_DB", str(Path(__file__).parent / "iap_social.db"))


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = _conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                post_type TEXT NOT NULL DEFAULT 'general',
                topic TEXT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                posted_at TEXT,
                mastodon_url TEXT,
                mastodon_id TEXT,
                mastodon_created_at TEXT
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_posts_created_at ON posts(created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_posts_posted_at ON posts(posted_at)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mastodon_replied (
                notification_id TEXT PRIMARY KEY,
                status_id TEXT NOT NULL,
                replied_at TEXT NOT NULL
            )
        """)


def insert_post(
    platform: str,
    content: str,
    post_type: str = "general",
    topic: Optional[str] = None,
) -> dict[str, Any]:
    """Insert a generated post. Returns the new row as dict."""
    now = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO posts (platform, post_type, topic, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (platform, post_type, topic or "", content, now),
        )
        row_id = cur.lastrowid
    return get_post(row_id)


def get_post(post_id: int) -> Optional[dict[str, Any]]:
    """Fetch a single post by id."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if row is None:
        return None
    return dict(row)


def list_posts(
    limit: int = 50,
    offset: int = 0,
    posted_only: Optional[bool] = None,
) -> list[dict[str, Any]]:
    """List posts, optionally filtered by posted status."""
    with get_db() as conn:
        q = "SELECT * FROM posts"
        params: list[Any] = []
        if posted_only is True:
            q += " WHERE posted_at IS NOT NULL"
        elif posted_only is False:
            q += " WHERE posted_at IS NULL"
        q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def mark_posted(
    post_id: int,
    mastodon_url: str,
    mastodon_id: str,
    mastodon_created_at: str,
) -> None:
    """Mark a post as posted to Mastodon."""
    now = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        conn.execute(
            """
            UPDATE posts
            SET posted_at = ?, mastodon_url = ?, mastodon_id = ?, mastodon_created_at = ?
            WHERE id = ?
            """,
            (now, mastodon_url, mastodon_id, mastodon_created_at, post_id),
        )


def mastodon_replied_record(notification_id: str, status_id: str) -> None:
    """Record that we replied to a Mastodon notification."""
    now = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO mastodon_replied (notification_id, status_id, replied_at) VALUES (?, ?, ?)",
            (notification_id, status_id, now),
        )


def mastodon_replied_ids() -> set[str]:
    """Return set of notification_ids we have already replied to."""
    with get_db() as conn:
        rows = conn.execute("SELECT notification_id FROM mastodon_replied").fetchall()
    return {r[0] for r in rows}
