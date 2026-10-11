# Qingwen

AI 私人教练 · 多 Agent 协作健身规划系统

## 技术栈
- 后端：FastAPI + AgentScope（Phase 2 起）
- 前端：React + Vite（Phase 4 起）
- 数据库：PostgreSQL + Redis（Phase 1 起）
- LLM：DeepSeek / 通义千问

## 开发路线
Phase 0 项目重组 → Phase 1 数据层 → Phase 2 多Agent
→ Phase 3 API 重构 → Phase 4 前端 → Phase 5 增强 → Phase 6 部署

## 本地启动（后端开发）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload