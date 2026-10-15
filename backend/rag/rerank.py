"""DashScope gte-rerank 精排。

把向量召回的 top-N 用交叉编码器重新打分，返回 top-K。
"""
import os

import dashscope

RERANK_MODEL = "gte-rerank-v2"


async def rerank(
    query: str,
    documents: list[str],
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """对候选文档精排。

    Args:
        query: 用户查询
        documents: 候选文档正文列表
        top_k: 返回数量

    Returns:
        [(原始索引, 相关性得分), ...] 按得分降序
    """
    if not documents:
        return []

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY 未设置")

    resp = dashscope.TextReRank.call(
        model=RERANK_MODEL,
        query=query,
        documents=documents,
        top_n=top_k,
        return_documents=False,
        api_key=api_key,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"DashScope rerank 失败: {resp.code} {resp.message}"
        )

    # 返回格式：[{'index': 0, 'relevance_score': 0.95}, ...]
    results = resp.output.get("results", [])
    return [
        (item["index"], float(item["relevance_score"]))
        for item in results
    ]