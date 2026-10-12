"""向量检索。使用 pgvector 的余弦距离。"""
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag.embedding import embed_query


@dataclass
class Chunk:
    id: int
    title: str
    content: str
    source: str
    metadata: dict
    similarity: float  # 0~1，越高越相关


async def search(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
    source: str | None = None,
    min_similarity: float = 0.3,
) -> list[Chunk]:
    """向量检索。返回按相似度降序的 chunk 列表。"""
    query_vec = embed_query(query)
    vec_str = "[" + ",".join(f"{v:.6f}" for v in query_vec) + "]"

    sql = """
        SELECT id, title, content, source, metadata,
               1 - (embedding <=> CAST(:vec AS vector)) AS similarity
        FROM knowledge_chunks
        WHERE embedding IS NOT NULL
    """
    params: dict = {"vec": vec_str, "k": top_k, "min_sim": min_similarity}
    if source is not None:
        sql += " AND source = :source"
        params["source"] = source
    sql += " AND 1 - (embedding <=> CAST(:vec AS vector)) >= :min_sim"
    sql += " ORDER BY embedding <=> CAST(:vec AS vector) LIMIT :k"

    result = await db.execute(text(sql), params)
    rows = result.fetchall()
    return [
        Chunk(
            id=row.id,
            title=row.title or "",
            content=row.content,
            source=row.source,
            metadata=row.metadata or {},
            similarity=float(row.similarity),
        )
        for row in rows
    ]