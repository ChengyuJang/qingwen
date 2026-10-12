"""通义千问 text-embedding-v3 客户端封装。

- 批量请求（DashScope 一次最多 25 条）
- 每条 1024 维向量
- 用于 RAG 检索
"""
import os
from typing import Iterable

import dashscope

DASHSCOPE_BATCH_SIZE = 10  # DashScope 单次调用上限
EMBEDDING_DIM = 1024


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量把文本列表转成 1024 维向量。自动分批。"""
    if not texts:
        return []

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY 未设置")

    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), DASHSCOPE_BATCH_SIZE):
        batch = texts[i : i + DASHSCOPE_BATCH_SIZE]
        resp = dashscope.TextEmbedding.call(
            model="text-embedding-v3",
            input=batch,
            api_key=api_key,
            dimension=EMBEDDING_DIM,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"DashScope embedding 失败: {resp.code} {resp.message}"
            )
        # resp.output.embeddings 是按输入顺序的列表
        for item in resp.output["embeddings"]:
            all_embeddings.append(item["embedding"])

    if len(all_embeddings) != len(texts):
        raise RuntimeError(
            f"embedding 数量不一致: 期望 {len(texts)}, 实际 {len(all_embeddings)}"
        )
    return all_embeddings


def embed_query(text: str) -> list[float]:
    """单条 query 的 embedding。"""
    return embed_texts([text])[0]