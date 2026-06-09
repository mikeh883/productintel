from dataclasses import dataclass

from sqlalchemy import select

from .db import SessionLocal
from .embeddings import embed_query
from .models import Document, DocumentChunk


@dataclass
class ChunkHit:
    title: str
    source: str
    content: str
    distance: float


def search(query: str, k: int = 5) -> list[ChunkHit]:
    """Cosine-similarity search over document chunks using pgvector (ADR 0007)."""
    query_embedding = embed_query(query)
    distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")

    with SessionLocal() as session:
        rows = session.execute(
            select(DocumentChunk.content, Document.title, Document.source, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .order_by(distance)
            .limit(k)
        ).all()

    return [
        ChunkHit(title=row.title, source=row.source, content=row.content, distance=float(row.distance))
        for row in rows
    ]
