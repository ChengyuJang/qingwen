# 轻问 · 面试准备 · 架构与技术问答

> 本文档整理面试高频问题的标准回答，覆盖 Tool/Skill/协议、多 Agent 架构、RAG 实验、上下文管理等。

---

## Q1: 项目涉及 Tool / Skill 吗？区别是什么？

### 概念区分

| 概念 | 定义 | 类比 |
|---|---|---|
| **Tool** | Agent 可调用的原子能力（抽象） | "锤子" |
| **Function** | Tool 的具体代码实现 | "8 号铁锤，带防滑柄" |
| **Skill** | 复合能力：多个 Tool + 知识 + prompt 的组合 | "会用锤子钉钉子"（知道何时用、怎么握、失败怎么办） |

### 项目实现

**Tool 层（已做）**——用 AgentScope 的 `FunctionTool` 注册：

| 工具 | 归属 Agent | 类型 |
|---|---|---|
| `fitness_calc` | Training / Nutrition | 本地 Python 函数 |
| `search_knowledge` | Training | RAG 检索工具 |
| `TeamAssign` | Orchestrator | AgentScope 内置（TeamPipeline 自动注入） |

代码位置：`backend/app/agents/tools.py`

```python
await t.add_tool(FunctionTool(fitness_calc, is_read_only=True))
await t.add_tool(FunctionTool(search_knowledge, is_read_only=True))