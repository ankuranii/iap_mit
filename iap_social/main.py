"""
FastAPI app for iap_social: generate & post Widvid content, backed by SQLite.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from database import (
    get_post,
    init_db,
    insert_post,
    list_posts,
    mark_posted,
)

load_dotenv()

app = FastAPI(
    title="IAP Social",
    description="Generate and post Widvid social content; persistence via SQLite.",
    version="1.0.0",
)


# --- Pydantic models ---


class GenerateRequest(BaseModel):
    platform: str = Field(default="twitter", description="twitter, linkedin, instagram, facebook")
    post_type: str = Field(default="general", description="general, product, technology, use_case, announcement, educational")
    topic: Optional[str] = Field(default=None, description="Optional focus topic")


class PostResponse(BaseModel):
    id: int
    platform: str
    post_type: str
    topic: Optional[str]
    content: str
    created_at: str
    posted_at: Optional[str]
    mastodon_url: Optional[str]
    mastodon_id: Optional[str]
    mastodon_created_at: Optional[str]


class GenerateResponse(BaseModel):
    post: PostResponse
    message: str = "Post generated and saved."


# --- Lifecycle ---


@app.on_event("startup")
def startup() -> None:
    init_db()


# --- Routes ---


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "iap_social"}


@app.get("/posts", response_model=list[PostResponse])
def api_list_posts(
    limit: int = 50,
    offset: int = 0,
    posted_only: Optional[bool] = None,
) -> list[PostResponse]:
    """List stored posts, optionally filter by posted status."""
    rows = list_posts(limit=limit, offset=offset, posted_only=posted_only)
    return [PostResponse(**r) for r in rows]


@app.get("/posts/{post_id}", response_model=PostResponse)
def api_get_post(post_id: int) -> PostResponse:
    """Fetch a single post by id."""
    row = get_post(post_id)
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse(**row)


def _load_widvid_docs() -> str:
    """Load knowledge-base docs from Notion API (replaces local WIDVID_OVERVIEW.md)."""
    try:
        from notion_docs import fetch_docs_from_notion
        return fetch_docs_from_notion()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch docs from Notion: {e}",
        )


@app.post("/posts/generate", response_model=GenerateResponse)
def api_generate_post(req: GenerateRequest) -> GenerateResponse:
    """Generate a post via OpenRouter, save to SQLite, and return it.
    Uses RAG (hybrid BM25 + semantic) over indexed docs for context when available;
    otherwise falls back to full Notion docs."""
    from generate_social_posts import generate_social_post
    from openai import OpenAI
    from rag import get_create_post_context

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY not set; cannot generate posts.",
        )

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    doc_content = get_create_post_context(
        req.platform,
        req.post_type,
        req.topic,
        top_k=5,
        keyword_weight=0.5,
        semantic_weight=0.5,
    )
    if not doc_content:
        doc_content = _load_widvid_docs()
    content = generate_social_post(
        client,
        doc_content,
        platform=req.platform,
        post_type=req.post_type,
        topic=req.topic,
    )
    if not content:
        content = (
            "🎬 Widvid turns text into video with AI. "
            "Diffusion models, 1080p, fast. Try it! #AIVideo #Widvid"
        )

    post = insert_post(
        platform=req.platform,
        content=content,
        post_type=req.post_type,
        topic=req.topic,
    )
    return GenerateResponse(post=PostResponse(**post))


@app.post("/posts/{post_id}/post-mastodon", response_model=PostResponse)
def api_post_to_mastodon(post_id: int) -> PostResponse:
    """Post an existing stored post to Mastodon and update DB."""
    from post_to_mastodon import post_to_mastodon, MASTODON_INSTANCE, MASTODON_ACCESS_TOKEN

    row = get_post(post_id)
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")

    if row.get("posted_at"):
        raise HTTPException(status_code=400, detail="Post already published to Mastodon.")

    if not MASTODON_ACCESS_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="MASTODON_ACCESS_TOKEN not set; cannot post to Mastodon.",
        )

    content = row["content"]
    if len(content) > 500:
        content = content[:497] + "..."

    result = post_to_mastodon(
        content,
        MASTODON_INSTANCE,
        MASTODON_ACCESS_TOKEN,
        image_path_or_url=None,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=result.get("error", "Mastodon API error"),
        )

    mark_posted(
        post_id,
        mastodon_url=result.get("url") or "",
        mastodon_id=str(result.get("id", "")),
        mastodon_created_at=result.get("created_at") or "",
    )
    updated = get_post(post_id)
    return PostResponse(**updated)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
