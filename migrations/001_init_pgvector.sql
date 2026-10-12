CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id          BIGSERIAL PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    source      TEXT NOT NULL,
    title       TEXT,
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}'::jsonb,
    embedding   vector(1024),
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_chunks_source ON knowledge_chunks (source);

CREATE INDEX IF NOT EXISTS idx_chunks_content_gin
    ON knowledge_chunks USING gin (to_tsvector('simple', content));