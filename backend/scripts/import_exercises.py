"""把动作库导入 knowledge_chunks 表。

用法（在 backend/ 目录下）：
    python -m scripts.import_exercises
"""
import asyncio
import json
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from rag.embedding import embed_texts

DATA_FILE = Path(__file__).parent.parent / "data" / "exercises.json"


async def main():
    exercises = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(f"加载 {len(exercises)} 条动作")

    # 构造 embedding 文本：name + description
    texts = [
        f"{e['name']}（目标肌群：{e['target']}，器械：{e['equipment']}，难度：{e['level']}）\n{e['description']}"
        for e in exercises
    ]

    print("开始生成 embedding（可能需要 10-30 秒）...")
    embeddings = embed_texts(texts)
    print(f"生成完成，共 {len(embeddings)} 条向量")

    async with AsyncSessionLocal() as db:
        # 清空旧数据（幂等导入）
        await db.execute(text("DELETE FROM knowledge_chunks WHERE source = 'exercise_lib'"))

        for e, content, emb in zip(exercises, texts, embeddings):
            emb_str = "[" + ",".join(f"{v:.6f}" for v in emb) + "]"
            await db.execute(
                text(
                    """
                    INSERT INTO knowledge_chunks
                        (doc_id, source, title, content, metadata, embedding)
                    VALUES
                        (:doc_id, :source, :title, :content,
                         CAST(:metadata AS jsonb),
                         CAST(:embedding AS vector))
                    """
                ),
                {
                    "doc_id": f"exercise:{e['name']}",
                    "source": "exercise_lib",
                    "title": e["name"],
                    "content": content,
                    "metadata": json.dumps(
                        {
                            "target": e["target"],
                            "equipment": e["equipment"],
                            "level": e["level"],
                        },
                        ensure_ascii=False,
                    ),
                    "embedding": emb_str,
                },
            )
        await db.commit()
    print(f"导入完成：{len(exercises)} 条")


if __name__ == "__main__":
    asyncio.run(main())