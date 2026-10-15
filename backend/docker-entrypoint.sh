#!/bin/sh
set -e

echo "=========================================="
echo " 轻问 · 后端启动"
echo "=========================================="

echo "[1/4] 运行数据库迁移..."
alembic upgrade head

echo "[2/4] 初始化 pgvector 表（幂等）..."
python -c "
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def init():
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id BIGSERIAL PRIMARY KEY,
                doc_id TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                content_seg TEXT,
                metadata JSONB DEFAULT '{}'::jsonb,
                embedding vector(1024),
                created_at TIMESTAMPTZ DEFAULT now()
            )
        '''))
        await conn.execute(text(
            'CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON knowledge_chunks '
            'USING hnsw (embedding vector_cosine_ops)'
        ))
        await conn.execute(text(
            'CREATE INDEX IF NOT EXISTS idx_chunks_source ON knowledge_chunks (source)'
        ))
        await conn.execute(text(
            'CREATE INDEX IF NOT EXISTS idx_chunks_content_seg_gin ON knowledge_chunks '
            \"USING gin (to_tsvector('simple', content_seg))\"
        ))
    await engine.dispose()
    print('  pgvector 表就绪')

asyncio.run(init())
"

echo "[3/4] 检查动作库数据..."
python -c "
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text('SELECT COUNT(*) FROM knowledge_chunks'))
        n = r.scalar()
        print(f'  当前 {n} 条')
        if n == 0:
            print('  表为空，自动导入种子数据...')
            import subprocess
            subprocess.run(['python', '-m', 'scripts.import_exercises'], check=False)

asyncio.run(check())
"

echo "[4/4] 启动服务..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1