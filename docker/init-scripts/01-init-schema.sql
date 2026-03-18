-- PostgreSQL 初始化脚本
-- 自动在容器首次启动时执行

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 实验表
CREATE TABLE IF NOT EXISTS experiments (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    strategy VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    config JSONB,
    metrics JSONB,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模型表
CREATE TABLE IF NOT EXISTS models (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    strategy VARCHAR(128) NOT NULL,
    version INTEGER NOT NULL,
    experiment_id VARCHAR(64) REFERENCES experiments(id) ON DELETE SET NULL,
    metrics JSONB,
    model_path VARCHAR(512),
    model_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 训练任务表
CREATE TABLE IF NOT EXISTS training_tasks (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(128) NOT NULL,
    steps INTEGER NOT NULL,
    status VARCHAR(32) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    experiment_id VARCHAR(64) REFERENCES experiments(id) ON DELETE SET NULL,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(128) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Key 表
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(128),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

-- 行情数据表（按日期分区的基础表）
CREATE TABLE IF NOT EXISTS stock_daily (
    ts_code VARCHAR(32) NOT NULL,
    trade_date DATE NOT NULL,
    open NUMERIC(10, 4),
    high NUMERIC(10, 4),
    low NUMERIC(10, 4),
    close NUMERIC(10, 4),
    pre_close NUMERIC(10, 4),
    change NUMERIC(10, 4),
    pct_chg NUMERIC(8, 4),
    vol NUMERIC(18, 2),
    amount NUMERIC(18, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ts_code, trade_date)
) PARTITION BY RANGE (trade_date);

-- 训练指标记录表（用于记录训练过程中的 step-by-step 指标）
CREATE TABLE IF NOT EXISTS training_metrics (
    id BIGSERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES training_tasks(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    reward NUMERIC(12, 6),
    episode_length INTEGER,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_strategy ON experiments(strategy);
CREATE INDEX IF NOT EXISTS idx_experiments_created_at ON experiments(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_models_strategy ON models(strategy);
CREATE INDEX IF NOT EXISTS idx_models_experiment_id ON models(experiment_id);
CREATE INDEX IF NOT EXISTS idx_models_created_at ON models(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_training_tasks_status ON training_tasks(status);
CREATE INDEX IF NOT EXISTS idx_training_tasks_priority ON training_tasks(priority, created_at);
CREATE INDEX IF NOT EXISTS idx_training_tasks_strategy ON training_tasks(strategy);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);

CREATE INDEX IF NOT EXISTS idx_stock_daily_trade_date ON stock_daily(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_stock_daily_ts_code ON stock_daily(ts_code);

CREATE INDEX IF NOT EXISTS idx_training_metrics_task_id ON training_metrics(task_id);
CREATE INDEX IF NOT EXISTS idx_training_metrics_step ON training_metrics(step);

-- 创建自动更新 updated_at 的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用触发器
CREATE TRIGGER update_experiments_updated_at
    BEFORE UPDATE ON experiments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 创建分区表（最近 3 个月）
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
BEGIN
    FOR i IN 0..3 LOOP
        start_date := date_trunc('month', CURRENT_DATE) + (i * INTERVAL '1 month');
        end_date := start_date + INTERVAL '1 month';
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS stock_daily_%s PARTITION OF stock_daily
             FOR VALUES FROM (%L) TO (%L)',
            to_char(start_date, 'YYYY_MM'),
            start_date,
            end_date
        );
    END LOOP;
END $$;

-- 插入默认管理员用户（密码：admin123）
-- 实际生产环境请修改密码！
INSERT INTO users (username, email, password_hash, is_superuser)
VALUES (
    'admin',
    'admin@qframe.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu',
    TRUE
) ON CONFLICT (username) DO NOTHING;

COMMENT ON TABLE experiments IS '实验跟踪表';
COMMENT ON TABLE models IS '模型注册表';
COMMENT ON TABLE training_tasks IS '训练任务队列';
COMMENT ON TABLE users IS '用户表';
COMMENT ON TABLE api_keys IS 'API 密钥表';
COMMENT ON TABLE stock_daily IS '股票日线行情（分区表）';
COMMENT ON TABLE training_metrics IS '训练过程指标';
