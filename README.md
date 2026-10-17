# 轻问 · 你的 AI 健身规划 Agent

> 让减脂轻一点，让改变问出来。

一个多 Agent 协作的 AI 健身规划系统。用户与「轻问」对话，后端由 **Orchestrator** 协调 4 个专业 Agent（信息采集 / 训练 / 营养 / 恢复）生成个性化方案，搭配 RAG 知识库检索。

🔗 **在线体验**：https://qingwen.vercel.app
📖 **API 文档**：https://qingwen-backend.onrender.com/docs

> ⚠️ 部署在 Render 免费层，首次访问有 50 秒冷启动。

---

## ✨ 核心特性

### 多 Agent 协作
- **Orchestrator** 判断意图，通过 `TeamAssign` 工具派活
- **4 个专家 Agent** 各带独立 system_prompt 和工具集：
  - **Intake** 信息采集
  - **Training** 训练方案（配 `fitness_calc` + `search_knowledge` 工具）
  - **Nutrition** 饮食建议
  - **Recovery** 恢复指导
- **Report Agent** 独立生成周报/月报

### 上下文管理（两层）
- **滑动窗口**：每次请求带最近 10 条历史
- **用户画像**：LLM 异步提取身高/体重/目标，存 `user_profiles`，跨会话记忆

### RAG 知识库
- **pgvector** + 通义 `text-embedding-v3`（1024 维）
- 94 条中文健身动作，HNSW 向量索引
- 提供 `search_knowledge` 工具供 Agent 调用

### 工程实践
- **SSE 流式**：逐 token 推送，前端按 Agent 分组渲染卡片
- **JWT 双 Token 认证** + Redis 限流（滑动窗口）
- **structlog 结构化埋点**：LLM 调用 token/耗时/工具调用全链路追踪
- **Docker 化**：一键 `docker compose up -d` 本地启动

---

## 🎯 效果评估

### Agent 路由准确率
14 条测试集，覆盖 4 类派活场景 + 3 类不派活场景。

| 指标 | 数值 |
|---|---|
| 严格准确率 | **85.7%** (12/14) |
| 无错派率 | 100% |

### RAG 检索
94 条知识库，30 条测试集，K=5。

| 方案 | Recall@5 | MRR | 结论 |
|---|---|---|---|
| **纯向量（采用）** | **0.967** | **0.800** | ✅ |
| 向量 + BM25（混合） | 0.967 | 0.734 | ❌ 中文分词噪声 |
| 向量 + Rerank | 0.967 | 0.772 | ❌ 通用模型不适配 |

> 详细实验记录见 [`backend/docs/rag_experiments.md`](backend/docs/rag_experiments.md)

---

## 🏗️ 技术栈

| 层 | 选型 |
|---|---|
| **后端** | FastAPI · SQLAlchemy 2.0（async） · AgentScope |
| **LLM** | 通义千问（qwen-plus / qwen-max） |
| **Embedding** | 通义 text-embedding-v3 |
| **数据库** | PostgreSQL 16 + pgvector |
| **缓存** | Redis 7 |
| **前端** | React 18 · TypeScript · Vite · Zustand · Recharts |
| **部署** | Render（后端）· Vercel（前端）· Upstash（Redis）· Docker |

---

## 🔄 架构

```mermaid
flowchart TD
    User[用户] -->|SSE| FE[React 前端]
    FE -->|/api/chat/stream| BE[FastAPI 后端]
    
    BE --> Auth{JWT 认证}
    Auth -->|通过| History[加载历史 + 用户画像]
    History --> Team[AgentScope TeamPipeline]
    
    Team --> Orchestrator[Orchestrator 协调者]
    Orchestrator -->|TeamAssign| Intake[Intake 采集]
    Orchestrator -->|TeamAssign| Training[Training 训练]
    Orchestrator -->|TeamAssign| Nutrition[Nutrition 营养]
    Orchestrator -->|TeamAssign| Recovery[Recovery 恢复]
    
    Training -->|search_knowledge| RAG[(pgvector 知识库)]
    Training -->|fitness_calc| Calc[本地计算]
    
    Intake --> DB[(PostgreSQL)]
    Training --> DB
    Nutrition --> DB
    Recovery --> DB
    BE --> Redis[(Redis 限流)]