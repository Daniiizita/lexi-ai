CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela de jobs de tradução
CREATE TABLE translation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    source_lang VARCHAR(10) DEFAULT 'en',
    target_lang VARCHAR(10) DEFAULT 'pt-BR',
    
    -- S3/MinIO paths
    source_path TEXT,
    translated_path TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- Métricas
    total_chunks INTEGER,
    chunks_translated INTEGER DEFAULT 0,
    model_name VARCHAR(100),
    translation_time_seconds FLOAT,
    
    -- Auditoria
    user_id VARCHAR(100),
    ip_address INET
);

CREATE INDEX idx_jobs_status ON translation_jobs(status);
CREATE INDEX idx_jobs_created_at ON translation_jobs(created_at DESC);

-- Tabela de chunks individuais
CREATE TABLE translation_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES translation_jobs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    
    source_text TEXT NOT NULL,
    translated_text TEXT,
    
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Decisões de tradução (JSON)
    decisions JSONB,
    terms_used JSONB,
    flags JSONB
);

CREATE INDEX idx_chunks_job_id ON translation_chunks(job_id);
CREATE INDEX idx_chunks_status ON translation_chunks(status);