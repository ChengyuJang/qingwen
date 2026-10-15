# RAG 检索实验记录

**测试环境**  
- 知识库：94 条中文健身动作（exercise_lib）
- 测试集：30 条 query，K=5
- Embedding：通义 text-embedding-v3（1024 维）
- 向量库：PostgreSQL + pgvector（HNSW 索引）

---

## 实验结果

| 方案 | Recall@5 | Hit Rate | MRR | 结论 |
|---|---|---|---|---|
| **纯向量（baseline）** | **0.967** | **0.569** | **0.800** | ✅ **最终采用** |
| 向量 + BM25（等权 RRF） | 0.900 | 0.492 | 0.636 | ❌ 噪声拖累 |
| 向量 + BM25（加权 RRF 0.85/0.15） | 0.967 | 0.522 | 0.734 | ❌ MRR 下降 |
| 纯向量 + gte-rerank-v2 精排 | 0.967 | — | 0.772 | ❌ 排序反而变差 |

---

## 分析

### 混合检索为何失败

- 中文分词问题：jieba 对健身术语分词不准（"卧推" 切成 "卧 / 推"）
- OR 逻辑召回噪声大：一次 query 命中几十条相关度低的文档
- 加权融合仍拖累向量路的排序质量

### Rerank 为何失败

- 通用 rerank 模型对领域专有名词理解弱
- Query（短，8-10 字）与 Document（长，100+ 字）长度不匹配
- `title：content` 拼接后无关信息干扰判断

### 纯向量为何最好

- 通义 embedding 对中文词嵌入做过优化，捕捉了健身术语语义
- 小规模知识库（<100 条）下，语义匹配已经足够
- 不引入额外的排序层，减少噪声来源

---

## 保留代码

三种方案都作为开关保留在 `backend/rag/retriever.py`：

```python
async def search(
    db,
    query,
    top_k=5,
    use_hybrid: bool = False,   # 混合检索（实验）
    use_rerank: bool = False,   # Rerank 精排（实验）
)

## 复现方式

# 纯向量（默认）
docker compose exec backend python -m scripts.eval_rag

# 混合检索
docker compose exec backend python -c "
import asyncio, json
from pathlib import Path
from app.db.session import AsyncSessionLocal
from rag.retriever import search

async def main():
    cases = json.loads(Path('data/rag_eval_set.json').read_text(encoding='utf-8'))
    async with AsyncSessionLocal() as db:
        for c in cases:
            await search(db, c['query'], top_k=5, use_hybrid=True)

asyncio.run(main())
"


---

## 存好后

**① 重启后端 + 确认基线**：

```powershell
cd D:\pycharm\PythonProject3\Qingwen
docker compose restart backend
docker compose exec backend python -m scripts.eval_rag