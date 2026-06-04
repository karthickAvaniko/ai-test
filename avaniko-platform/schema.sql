-- ═══════════════════════════════════════════
-- AVANIKO AI PLATFORM — PostgreSQL Schema
-- ═══════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Users ────────────────────────────────────────────────
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(255) NOT NULL,
    password    VARCHAR(255) NOT NULL,          -- bcrypt hashed
    role        VARCHAR(20) DEFAULT 'user',     -- user | admin
    is_active   BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── API Keys ─────────────────────────────────────────────
CREATE TABLE api_keys (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash      VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 of actual key
    key_prefix    VARCHAR(20) NOT NULL,         -- ava-sk-XXXXXXXX (first 20 chars shown)
    name          VARCHAR(100) NOT NULL DEFAULT 'Default Key',
    is_active     BOOLEAN DEFAULT TRUE,
    daily_limit   INTEGER DEFAULT 1000,
    monthly_limit INTEGER DEFAULT 30000,
    requests_today INTEGER DEFAULT 0,
    requests_month INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    total_tokens   BIGINT DEFAULT 0,
    last_used_at   TIMESTAMPTZ,
    expires_at     TIMESTAMPTZ,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ── AI Models Registry ───────────────────────────────────
CREATE TABLE models (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id       VARCHAR(100) UNIQUE NOT NULL,  -- 'qwen3-moe', 'llama-3', etc.
    name           VARCHAR(200) NOT NULL,
    provider       VARCHAR(50) NOT NULL,           -- runpod | anthropic | google | openai
    provider_url   TEXT,                           -- encrypted backend URL
    provider_key   TEXT,                           -- encrypted provider API key
    context_length INTEGER DEFAULT 32768,
    input_cost     DECIMAL(10,6) DEFAULT 0,       -- cost per 1K tokens (for billing)
    output_cost    DECIMAL(10,6) DEFAULT 0,
    is_active      BOOLEAN DEFAULT TRUE,
    capabilities   TEXT[] DEFAULT ARRAY['chat'],   -- chat | code | vision | embeddings
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ── Usage Logs ───────────────────────────────────────────
CREATE TABLE usage_logs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id       UUID REFERENCES api_keys(id),
    user_id          UUID REFERENCES users(id),
    model_id         VARCHAR(100),
    endpoint         VARCHAR(200) NOT NULL,
    prompt_tokens    INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens     INTEGER DEFAULT 0,
    response_time_ms INTEGER DEFAULT 0,
    status_code      INTEGER DEFAULT 200,
    status           VARCHAR(20) DEFAULT 'success',
    cost             DECIMAL(10,6) DEFAULT 0,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── Request Logs ─────────────────────────────────────────
CREATE TABLE request_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id      UUID REFERENCES api_keys(id),
    user_id         UUID REFERENCES users(id),
    method          VARCHAR(10) NOT NULL,
    endpoint        VARCHAR(200) NOT NULL,
    request_body    JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Billing ──────────────────────────────────────────────
CREATE TABLE billing (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID NOT NULL REFERENCES users(id),
    period_start     DATE NOT NULL,
    period_end       DATE NOT NULL,
    total_tokens     BIGINT DEFAULT 0,
    total_requests   INTEGER DEFAULT 0,
    total_cost       DECIMAL(10,4) DEFAULT 0,
    status           VARCHAR(20) DEFAULT 'pending',  -- pending | paid | overdue
    invoice_url      TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── Projects ─────────────────────────────────────────────
CREATE TABLE projects (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id    VARCHAR(60) UNIQUE NOT NULL,
    name          VARCHAR(200) NOT NULL,
    description   TEXT DEFAULT '',
    system_prompt TEXT NOT NULL,
    model_id      VARCHAR(100) DEFAULT 'qwen3-moe',
    temperature   FLOAT DEFAULT 0.7,
    max_tokens    INTEGER DEFAULT 4096,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────
CREATE INDEX idx_api_keys_user_id    ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash   ON api_keys(key_hash);
CREATE INDEX idx_usage_api_key       ON usage_logs(api_key_id);
CREATE INDEX idx_usage_user          ON usage_logs(user_id);
CREATE INDEX idx_usage_created       ON usage_logs(created_at DESC);
CREATE INDEX idx_request_logs_key    ON request_logs(api_key_id);
CREATE INDEX idx_request_logs_created ON request_logs(created_at DESC);
CREATE INDEX idx_projects_user       ON projects(user_id);

-- ── Auto-update updated_at ────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated    BEFORE UPDATE ON users    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_projects_updated BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── Daily reset function ─────────────────────────────────
CREATE OR REPLACE FUNCTION reset_daily_counts() RETURNS void AS $$
BEGIN UPDATE api_keys SET requests_today = 0; END;
$$ LANGUAGE plpgsql;

-- ── Seed default models ──────────────────────────────────
INSERT INTO models (model_id, name, provider, context_length, capabilities) VALUES
    ('qwen3-moe',     'Qwen3 MoE',           'runpod',    32768, ARRAY['chat','code','vision']),
    ('llama-3.1-70b', 'Llama 3.1 70B',       'runpod',    32768, ARRAY['chat','code']),
    ('claude-3-5-sonnet', 'Claude 3.5 Sonnet','anthropic', 200000, ARRAY['chat','code','vision']),
    ('gemini-1.5-pro',    'Gemini 1.5 Pro',  'google',    1000000, ARRAY['chat','code','vision'])
ON CONFLICT (model_id) DO NOTHING;
