"""
RAG retrieval for create-posts context: BM25 (FTS5) + semantic search, hybrid ranking.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

RAG_DB_PATH = os.environ.get(
    "IAP_SOCIAL_RAG_DB",
    str(Path(__file__).resolve().parent / "rag.db"),
)

# Lazy-loaded embedding model
_embedding_model: Any = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for text (384-dim, all-MiniLM-L6-v2)."""
    model = _get_embedding_model()
    emb = model.encode(text, convert_to_numpy=True)
    return emb.tolist()


def _rag_conn() -> sqlite3.Connection:
    return sqlite3.connect(RAG_DB_PATH)


def init_rag_db(conn: sqlite3.Connection | None = None) -> None:
    """Create RAG tables: embeddings_meta, FTS5 embeddings_fts. Same rowids for both."""
    own = conn is None
    if own:
        conn = _rag_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                embedding_json TEXT
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_fts USING fts5(
                content,
                tokenize='porter'
            )
        """)
        conn.commit()
    finally:
        if own:
            conn.close()


def bm25_search(conn: sqlite3.Connection, query: str, limit: int = 100) -> dict[int, float]:
    """
    Search using BM25 ranking via FTS5.
    Returns dict mapping embedding_id (rowid) to raw BM25 score.
    FTS5 BM25 scores are NEGATIVE (more negative = better match).
    """
    cursor = conn.cursor()
    safe_query = query.replace('"', '""')
    try:
        cursor.execute("""
            SELECT rowid, bm25(embeddings_fts) AS score
            FROM embeddings_fts
            WHERE embeddings_fts MATCH ?
            LIMIT ?
        """, (safe_query, limit))
        return {row[0]: row[1] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        return {}


def normalize_bm25_scores(bm25_scores: dict[int, float]) -> dict[int, float]:
    """
    Normalize BM25 scores to [0, 1]. FTS5 BM25 is negative (more negative = better).
    Invert so best match → 1.0, worst → 0.0.
    """
    if not bm25_scores:
        return {}
    scores = list(bm25_scores.values())
    min_s, max_s = min(scores), max(scores)
    if min_s == max_s:
        return {i: 1.0 for i in bm25_scores}
    r = max_s - min_s
    return {i: (max_s - s) / r for i, s in bm25_scores.items()}


def normalize_distances(distances: dict[int, float]) -> dict[int, float]:
    """
    Normalize cosine distances to similarity scores in [0, 1].
    Distance in [0, 2], 0 = identical. Convert to similarity 1 - (d/2), then normalize.
    """
    if not distances:
        return {}
    sim = {i: 1 - (d / 2) for i, d in distances.items()}
    min_s, max_s = min(sim.values()), max(sim.values())
    if min_s == max_s:
        return {i: 1.0 for i in sim}
    r = max_s - min_s
    return {i: (s - min_s) / r for i, s in sim.items()}


def get_metadata_by_ids(conn: sqlite3.Connection, ids: list[int]) -> dict[int, dict]:
    """Fetch metadata for given IDs from embeddings_meta."""
    if not ids:
        return {}
    cur = conn.cursor()
    ph = ",".join("?" * len(ids))
    cur.execute(f"""
        SELECT id, source_type, source_id, content, metadata
        FROM embeddings_meta
        WHERE id IN ({ph})
    """, ids)
    out = {}
    for row in cur.fetchall():
        out[row[0]] = {
            "source_type": row[1],
            "source_id": row[2],
            "content": row[3],
            "metadata": json.loads(row[4]) if row[4] else {},
        }
    return out


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    import math
    sa = sum(x * x for x in a) ** 0.5
    sb = sum(x * x for x in b) ** 0.5
    if sa == 0 or sb == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (sa * sb)


def semantic_search(
    conn: sqlite3.Connection,
    query_embedding: list[float],
    limit: int = 100,
) -> dict[int, float]:
    """
    Approximate semantic search over stored embeddings.
    Returns dict mapping id → cosine *distance* (1 - similarity), 0 = identical.
    """
    cur = conn.cursor()
    cur.execute("SELECT id, embedding_json FROM embeddings_meta WHERE embedding_json IS NOT NULL")
    rows = cur.fetchall()
    if not rows:
        return {}
    scored = []
    for i, jstr in rows:
        emb = json.loads(jstr)
        sim = _cosine_similarity(query_embedding, emb)
        dist = 1 - sim  # distance in [0, 2]
        scored.append((i, dist))
    scored.sort(key=lambda x: x[1])
    return {i: d for i, d in scored[:limit]}


def hybrid_search(
    conn: sqlite3.Connection,
    query: str,
    query_embedding: list[float],
    keyword_weight: float = 0.5,
    semantic_weight: float = 0.5,
    top_k: int = 10,
) -> list[dict]:
    """
    Hybrid search: BM25 + semantic. final_score = kw * bm25_norm + sem * semantic_norm.
    Returns list of {id, content, source_type, source_id, metadata, bm25_score, semantic_score, final_score}.
    """
    bm25_raw = bm25_search(conn, query)
    bm25_norm = normalize_bm25_scores(bm25_raw)
    sem_raw = semantic_search(conn, query_embedding, limit=100)
    sem_norm = normalize_distances(sem_raw)
    all_ids = set(bm25_norm.keys()) | set(sem_norm.keys())
    if not all_ids:
        return []
    meta = get_metadata_by_ids(conn, list(all_ids))
    results = []
    for i in all_ids:
        bm = bm25_norm.get(i, 0.0)
        sm = sem_norm.get(i, 0.0)
        final = keyword_weight * bm + semantic_weight * sm
        m = meta.get(i, {})
        results.append({
            "id": i,
            "content": m.get("content", ""),
            "source_type": m.get("source_type", ""),
            "source_id": m.get("source_id", ""),
            "metadata": m.get("metadata", {}),
            "bm25_score": bm,
            "semantic_score": sm,
            "final_score": final,
        })
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:top_k]


def index_chunks(
    conn: sqlite3.Connection,
    chunks: list[dict],
    source_type: str = "notion",
    source_id: str = "company",
) -> int:
    """
    Index chunk documents into embeddings_meta + embeddings_fts + embeddings.
    Each chunk: {content, metadata}. Returns number indexed.
    """
    count = 0
    for c in chunks:
        content = c.get("content", "")
        meta = c.get("metadata", {})
        if not content.strip():
            continue
        emb = generate_embedding(content)
        emb_json = json.dumps(emb)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO embeddings_meta (source_type, source_id, content, metadata, embedding_json)
            VALUES (?, ?, ?, ?, ?)
        """, (source_type, source_id, content, json.dumps(meta), emb_json))
        rowid = cur.lastrowid
        cur.execute(
            "INSERT INTO embeddings_fts(rowid, content) VALUES (?, ?)",
            (rowid, content),
        )
        count += 1
    conn.commit()
    return count


def format_context_for_prompt(
    results: list[dict],
    max_chars: int = 4000,
) -> str:
    """Format search results into context for the LLM prompt."""
    if not results:
        return "No relevant context found."

    context_parts = []
    chars_used = 0

    for i, result in enumerate(results, 1):
        header = f"[{i}. {result['source_type']}] (score: {result['final_score']:.2f})"
        content = result["content"]

        available = max_chars - chars_used - len(header) - 10
        if available <= 100:
            break

        if len(content) > available:
            content = content[: available - 3] + "..."

        entry = f"{header}\n{content}\n"
        context_parts.append(entry)
        chars_used += len(entry)

    return "\n".join(context_parts)


def retrieve_context(
    conn: sqlite3.Connection,
    query: str,
    top_k: int = 10,
    keyword_weight: float = 0.5,
    semantic_weight: float = 0.5,
    max_chars: int = 4000,
) -> tuple[str, list[dict]]:
    """High-level retrieve and format context for RAG. Returns (formatted_context, results)."""
    try:
        query_embedding = generate_embedding(query)
    except Exception:
        return "No relevant context found.", []
    results = hybrid_search(
        conn,
        query,
        query_embedding,
        keyword_weight=keyword_weight,
        semantic_weight=semantic_weight,
        top_k=top_k,
    )
    formatted = format_context_for_prompt(results, max_chars=max_chars)
    return formatted, results


def build_rag_context(
    conn: sqlite3.Connection,
    query: str,
    top_k: int = 5,
    keyword_weight: float = 0.5,
    semantic_weight: float = 0.5,
    max_chars: int = 4000,
) -> str:
    """
    Run hybrid RAG search and return formatted context for the LLM prompt.
    If no results, returns empty string (caller can fall back to full docs).
    """
    formatted, results = retrieve_context(
        conn,
        query,
        top_k=top_k,
        keyword_weight=keyword_weight,
        semantic_weight=semantic_weight,
        max_chars=max_chars,
    )
    if not results:
        return ""
    return formatted


def rag_count(conn: sqlite3.Connection) -> int:
    """Return number of indexed chunks."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM embeddings_meta")
    return cur.fetchone()[0]


def ensure_rag_indexed(
    conn: sqlite3.Connection | None = None,
    chunk_strategy: str = "paragraphs",
    max_chars: int = 500,
) -> bool:
    """
    Ensure RAG DB is initialized and populated. If no chunks exist, fetch Notion docs,
    chunk them, and index. Returns True if we have indexed chunks (now or already).
    """
    own = conn is None
    if own:
        conn = _rag_conn()
    try:
        init_rag_db(conn)
        if rag_count(conn) > 0:
            return True
        from notion_docs import fetch_docs_from_notion
        from chunking import chunk_document

        raw = fetch_docs_from_notion()
        chunks = chunk_document(
            raw,
            "notion_company",
            strategy=chunk_strategy,
            max_chars=max_chars,
        )
        n = index_chunks(conn, chunks, source_type="notion", source_id="company")
        return n > 0
    except Exception:
        return False
    finally:
        if own:
            conn.close()


def get_create_post_context(
    platform: str,
    post_type: str,
    topic: str | None,
    *,
    top_k: int = 5,
    keyword_weight: float = 0.5,
    semantic_weight: float = 0.5,
    max_chars: int = 4000,
) -> str:
    """
    RAG retrieval for create-posts. Builds query from platform/post_type/topic,
    runs hybrid search, returns formatted context for LLM prompt.
    Returns empty string if RAG unavailable or no results (caller should fall back to full docs).
    """
    query_parts = [platform, post_type]
    if topic:
        query_parts.append(topic)
    query = " ".join(query_parts)

    conn = _rag_conn()
    try:
        if not ensure_rag_indexed(conn):
            return ""
        return build_rag_context(
            conn,
            query,
            top_k=top_k,
            keyword_weight=keyword_weight,
            semantic_weight=semantic_weight,
            max_chars=max_chars,
        )
    except Exception:
        return ""
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    test_query = sys.argv[1] if len(sys.argv) > 1 else "AI consulting"
    conn = _rag_conn()
    init_rag_db(conn)
    print("BM25 search:", repr(test_query))
    bm25_results = bm25_search(conn, test_query)
    for emb_id, score in list(bm25_results.items())[:3]:
        print(f"  ID {emb_id}: score = {score:.4f}")
    print()
    context, results = retrieve_context(conn, test_query, top_k=10)
    print("Retrieved context:\n")
    print(context[:1500] + "..." if len(context) > 1500 else context)
    conn.close()
