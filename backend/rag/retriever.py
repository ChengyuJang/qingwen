"""混合检索：向量 + BM25 全文，用 RRF 融合。"""
from rag.rerank import rerank as rerank_fn
import jieba
from pathlib import Path as _Path
_FITNESS_DICT = _Path(__file__).parent.parent / "data" / "fitness_dict.txt"
if _FITNESS_DICT.exists():
    jieba.load_userdict(str(_FITNESS_DICT))
import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag.embedding import embed_query

RRF_K = 60  # RRF 平滑参数，标准值


@dataclass
class Chunk:
    id: int
    title: str
    content: str
    source: str
    metadata: dict
    similarity: float  # 融合后的得分（0~1，越高越相关）


async def _vector_search(
    db: AsyncSession, vec_str: str, limit: int, source: str | None
) -> list[tuple[int, float]]:
    """向量检索，返回 [(chunk_id, similarity), ...]"""
    sql = """
        SELECT id, 1 - (embedding <=> CAST(:vec AS vector)) AS sim
        FROM knowledge_chunks
        WHERE embedding IS NOT NULL
    """
    params: dict = {"vec": vec_str, "k": limit}
    if source:
        sql += " AND source = :source"
        params["source"] = source
    sql += " ORDER BY embedding <=> CAST(:vec AS vector) LIMIT :k"
    result = await db.execute(text(sql), params)
    return [(row.id, float(row.sim)) for row in result.all()]


async def _bm25_search(
    db: AsyncSession, query: str, limit: int, source: str | None
) -> list[int]:
    """BM25 全文检索：优先 AND（精确），退化到 OR（宽松）。"""
    raw_words = [w.strip() for w in jieba.cut(query) if w.strip()]
    raw_words = [w for w in raw_words if re.match(r"^[\w\u4e00-\u9fa5]+$", w)]
    if not raw_words:
        return []

    long_words = [w for w in raw_words if len(w) >= 2]
    if long_words:
        words = long_words
    else:
        merged = []
        i = 0
        while i < len(raw_words):
            if i + 1 < len(raw_words):
                merged.append(raw_words[i] + raw_words[i + 1])
                i += 2
            else:
                merged.append(raw_words[i])
                i += 1
        words = merged

    # 只取最长的 2 个词（限制噪声）
    words = sorted(set(words), key=len, reverse=True)[:2]

    # 先试 AND：所有词都命中
    and_query = " & ".join(words)
    result = await _run_fts(db, and_query, limit, source)
    if result:
        return result

    # 退化到 OR：任一命中
    or_query = " | ".join(words)
    return await _run_fts(db, or_query, limit, source)


async def _run_fts(
    db: AsyncSession, tsquery_str: str, limit: int, source: str | None
) -> list[int]:
    sql = """
        SELECT id,
               ts_rank_cd(to_tsvector('simple', content_seg),
                          to_tsquery('simple', :q)) AS rank
        FROM knowledge_chunks
        WHERE content_seg IS NOT NULL
          AND to_tsvector('simple', content_seg) @@ to_tsquery('simple', :q)
    """
    params: dict = {"q": tsquery_str, "k": limit}
    if source:
        sql += " AND source = :source"
        params["source"] = source
    sql += " ORDER BY rank DESC LIMIT :k"
    result = await db.execute(text(sql), params)
    return [row.id for row in result.all()]


async def search(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
    source: str | None = None,
    min_similarity: float = 0.3,
    use_hybrid: bool = False,
    use_rerank: bool = False,
) -> list[Chunk]:
    """知识库检索。

    Args:
        use_hybrid: 是否启用「向量 + BM25」混合检索（实验功能）
        use_rerank: 是否启用 DashScope gte-rerank 精排（默认开启）
    """
    query_vec = embed_query(query)
    vec_str = "[" + ",".join(f"{v:.6f}" for v in query_vec) + "]"

    # 开启 rerank 时召回更多，留给精排发挥空间
    recall_k = max(top_k * 4, 20) if use_rerank else max(top_k * 3, 15)

    vector_hits = await _vector_search(db, vec_str, recall_k, source)
    vector_hits = [(cid, sim) for cid, sim in vector_hits if sim >= min_similarity]

    if use_hybrid:
        bm25_k = max(top_k, 5)
        bm25_ids = await _bm25_search(db, query, bm25_k, source)
        W_VECTOR = 0.85
        W_BM25 = 0.15
        rrf_scores: dict[int, float] = {}
        for rank, (cid, _) in enumerate(vector_hits):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + W_VECTOR / (RRF_K + rank + 1)
        for rank, cid in enumerate(bm25_ids):
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + W_BM25 / (RRF_K + rank + 1)
        if not rrf_scores:
            return []
        sorted_items = sorted(rrf_scores.items(), key=lambda x: -x[1])[:recall_k]
        candidate_ids = [cid for cid, _ in sorted_items]
        score_map = {cid: s for cid, s in sorted_items}
    else:
        candidate_ids = [cid for cid, _ in vector_hits]
        score_map = {cid: sim for cid, sim in vector_hits}

    if not candidate_ids:
        return []

    # 批量查回候选正文
    detail = await db.execute(
        text(
            "SELECT id, title, content, source, metadata "
            "FROM knowledge_chunks WHERE id = ANY(:ids)"
        ),
        {"ids": candidate_ids},
    )
    detail_map = {row.id: row for row in detail.all()}

    # ---------- Rerank 精排 ----------
    if use_rerank and len(candidate_ids) > top_k:
        # 按原顺序拼候选文本（title + content 一起给 rerank 判断）
        docs: list[str] = []
        valid_ids: list[int] = []
        for cid in candidate_ids:
            row = detail_map.get(cid)
            if row is None:
                continue
            docs.append(f"{row.title}：{row.content}")
            valid_ids.append(cid)

        try:
            ranked = await rerank_fn(query, docs, top_k=top_k)
            # ranked 返回 (在 docs 里的索引, score)
            final_ids = [valid_ids[idx] for idx, _ in ranked]
            # 用 rerank 得分归一化后作为 similarity
            if ranked:
                max_score = max(s for _, s in ranked) or 1.0
                score_map = {
                    valid_ids[idx]: s / max_score for idx, s in ranked
                }
        except Exception as e:
            # rerank 失败降级到向量顺序
            import structlog
            structlog.get_logger("rerank").warning(
                "rerank_failed_fallback", error=str(e)
            )
            final_ids = candidate_ids[:top_k]
    else:
        final_ids = candidate_ids[:top_k]

    # ---------- 拼装返回 ----------
    results: list[Chunk] = []
    for cid in final_ids:
        row = detail_map.get(cid)
        if row is None:
            continue
        results.append(
            Chunk(
                id=row.id,
                title=row.title or "",
                content=row.content,
                source=row.source,
                metadata=row.metadata or {},
                similarity=round(float(score_map.get(cid, 0.0)), 4),
            )
        )
    return results