import asyncio

from app.db.session import AsyncSessionLocal
from rag.retriever import search


async def main():
    queries = [
        "哑铃练腿的动作",
        "膝盖不好怎么做深蹲",
        "练胸的徒手动作",
        "引体向上怎么做",
    ]
    async with AsyncSessionLocal() as db:
        for q in queries:
            print(f"\n{'='*60}")
            print(f"Query: {q}")
            print(f"{'-'*60}")
            chunks = await search(db, q, top_k=3)
            if not chunks:
                print("  (无结果)")
            for c in chunks:
                print(f"  [{c.similarity:.3f}] {c.title}")


asyncio.run(main())