"""RAG 检索质量评估。

指标：
- Recall@K：前 K 条结果里命中至少一个期望文档的比例
- MRR：第一个正确结果的排名倒数平均
- Hit Rate：Top-K 里命中率

用法（在 backend/ 下）：
    python -m scripts.eval_rag
"""
import asyncio
import json
from pathlib import Path

from app.db.session import AsyncSessionLocal
from rag.retriever import search

EVAL_FILE = Path(__file__).parent.parent / "data" / "rag_eval_set.json"
K = 5


async def main():
    cases = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
    print(f"评估集：{len(cases)} 条，K={K}\n")

    total_recall = 0.0
    total_mrr = 0.0
    total_hit = 0.0
    details = []

    async with AsyncSessionLocal() as db:
        for case in cases:
            q = case["query"]
            expected = set(case["expected"])
            chunks = await search(db, q, top_k=K)
            got = [c.title for c in chunks]

            # 命中集合
            hits = [i for i, t in enumerate(got) if t in expected]

            recall = 1.0 if hits else 0.0
            mrr = 1.0 / (hits[0] + 1) if hits else 0.0
            hit_rate = len(set(got) & expected) / len(expected) if expected else 0.0

            total_recall += recall
            total_mrr += mrr
            total_hit += hit_rate
            details.append({
                "query": q,
                "expected": expected,
                "got": got,
                "hit_rank": hits[0] + 1 if hits else None,
            })

    n = len(cases)
    print(f"{'='*60}")
    print(f"Recall@{K}    : {total_recall/n:.3f}")
    print(f"Hit Rate    : {total_hit/n:.3f}")
    print(f"MRR         : {total_mrr/n:.3f}")
    print(f"{'='*60}\n")

    # 逐条详情
    for d in details:
        rank_str = f"排名 {d['hit_rank']}" if d["hit_rank"] else "❌ 未命中"
        print(f"[{rank_str}] {d['query']}")
        print(f"  期望：{sorted(d['expected'])}")
        print(f"  实际：{d['got']}\n")


if __name__ == "__main__":
    asyncio.run(main())