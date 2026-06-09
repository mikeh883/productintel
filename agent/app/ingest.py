"""Ingest a corpus of Markdown files into the knowledge base.

Usage (local):  uv run python -m app.ingest ../corpus
Usage (compose): docker compose exec agent python -m app.ingest /srv/corpus
"""

import pathlib
import sys

from .db import SessionLocal
from .embeddings import embed_texts
from .models import Document, DocumentChunk


def chunk_text(text: str, target: int = 1000) -> list[str]:
    """Naive paragraph-merge chunker. Good enough for v0; revisit with a real
    chunking strategy when retrieval quality matters."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > target:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return chunks


def ingest_dir(corpus_dir: str) -> None:
    root = pathlib.Path(corpus_dir)
    files = sorted(root.rglob("*.md"))
    if not files:
        print(f"No .md files found under {root.resolve()}")
        return

    with SessionLocal() as session:
        for path in files:
            text = path.read_text(encoding="utf-8")
            first_line = text.splitlines()[0] if text.strip() else ""
            title = first_line.lstrip("# ").strip() or path.stem
            chunks = chunk_text(text)
            if not chunks:
                continue
            embeddings = embed_texts(chunks)

            document = Document(title=title, source=path.name)
            session.add(document)
            session.flush()  # assign document.id

            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                session.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        content=chunk,
                        embedding=embedding,
                    )
                )
            print(f"Ingested {path.name}: {len(chunks)} chunks")
        session.commit()
    print("Done.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "../corpus"
    ingest_dir(target)
