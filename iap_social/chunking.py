"""
Chunk documents by fixed character count, paragraph boundaries, or sentence count.
"""

import re
from typing import Literal


def _extract_doc_title(content: str, filename: str) -> str:
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else filename


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences (roughly on . ! ? followed by space or end)."""
    # Split on sentence-ending punctuation followed by space or end; keep delim
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _split_paragraphs(content: str) -> list[str]:
    """Split on blank lines (paragraph boundaries)."""
    blocks = re.split(r"\n\s*\n", content)
    return [b.strip() for b in blocks if b.strip()]


def chunk_document(
    content: str,
    filename: str,
    *,
    strategy: Literal["chars", "paragraphs", "sentences"] = "chars",
    max_chars: int = 500,
    sentences_per_chunk: int = 5,
) -> list[dict]:
    """
    Chunk a document using one of three strategies:

    - **chars**: Fixed character count (~max_chars). Breaks at sentence boundaries
      when possible to avoid mid-sentence cuts.
    - **paragraphs**: Chunk by paragraph boundaries. Merges paragraphs into chunks
      up to ~max_chars; never splits within a paragraph.
    - **sentences**: Chunk by sentence count. Each chunk has up to
      sentences_per_chunk sentences.

    Each chunk includes optional document title (# header) context and metadata.
    """
    doc_title = _extract_doc_title(content, filename)
    # Strip leading # title line to avoid duplicating in header
    body = re.sub(r"^#\s+.+$", "", content.strip(), count=1, flags=re.MULTILINE).strip()
    header = f"[From: {filename}]\n# {doc_title}\n\n"

    def make_chunk(text: str, meta: dict) -> dict:
        return {
            "content": f"{header}{text}".strip(),
            "metadata": {"source_file": filename, **meta},
        }

    if strategy == "sentences":
        # Chunk by sentence count
        flat = body.replace("\n", " ").strip()
        sentences = _split_sentences(flat)
        chunks = []
        for i in range(0, len(sentences), sentences_per_chunk):
            batch = sentences[i : i + sentences_per_chunk]
            text = " ".join(batch)
            chunks.append(
                make_chunk(
                    text,
                    {
                        "strategy": "sentences",
                        "sentence_start": i,
                        "sentence_end": min(i + sentences_per_chunk, len(sentences)),
                    },
                )
            )
        return chunks if chunks else [make_chunk(body, {"strategy": "sentences"})]

    if strategy == "paragraphs":
        # Chunk by paragraph boundaries; merge paragraphs until ~max_chars
        paragraphs = _split_paragraphs(body)
        chunks = []
        current: list[str] = []
        current_len = 0
        for p in paragraphs:
            p_len = len(p) + (2 if current else 0)  # \n\n
            if current and current_len + p_len > max_chars:
                text = "\n\n".join(current)
                chunks.append(
                    make_chunk(
                        text,
                        {"strategy": "paragraphs", "char_count": len(text)},
                    )
                )
                current = []
                current_len = 0
            current.append(p)
            current_len += p_len
        if current:
            text = "\n\n".join(current)
            chunks.append(
                make_chunk(
                    text,
                    {"strategy": "paragraphs", "char_count": len(text)},
                )
            )
        return chunks if chunks else [make_chunk(body, {"strategy": "paragraphs"})]

    # strategy == "chars": fixed character count, break at sentence boundaries when possible
    flat = body.replace("\n", " ").strip()
    sentences = _split_sentences(flat)
    chunks = []
    current: list[str] = []
    current_len = 0
    for s in sentences:
        s_len = len(s) + (1 if current else 0)
        if current and current_len + s_len > max_chars:
            text = " ".join(current)
            chunks.append(
                make_chunk(
                    text,
                    {"strategy": "chars", "char_count": len(text)},
                )
            )
            current = []
            current_len = 0
        current.append(s)
        current_len += s_len
    if current:
        text = " ".join(current)
        chunks.append(
            make_chunk(
                text,
                {"strategy": "chars", "char_count": len(text)},
            )
        )
    return chunks if chunks else [make_chunk(body, {"strategy": "chars"})]


# ---------------------------------------------------------------------------
# Test chunking
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_doc = """
# Our Company

We are an AI consulting firm.

## Services

We offer enterprise AI strategy consulting.

## Team

Our team has 20 years of combined experience.
"""

    # Default: chars, max_chars=500 (like user example)
    chunks = chunk_document(sample_doc, "company.md")
    print(f"Document split into {len(chunks)} chunks (strategy=chars, max_chars=500):\n")
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i + 1} ---")
        print(chunk["content"][:200] + ("..." if len(chunk["content"]) > 200 else ""))
        print()

    # All strategies
    for strategy in ("chars", "paragraphs", "sentences"):
        cs = chunk_document(
            sample_doc, "company.md",
            strategy=strategy,
            max_chars=500,
            sentences_per_chunk=3,
        )
        print(f"[{strategy}] {len(cs)} chunks")
