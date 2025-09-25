-- STRATUS Bug Advisor Database Schema
-- SQLite compatible schema with PostgreSQL extensions commented

-- Query logging for analytics
CREATE TABLE query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Use SERIAL for PostgreSQL
    product VARCHAR(50) NOT NULL,
    query_text TEXT NOT NULL,
    query_length INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    query_hash VARCHAR(64) -- For privacy and deduplication
);

-- User feedback collection
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Use SERIAL for PostgreSQL
    query_id INTEGER,
    query_hash VARCHAR(64), -- hashed for privacy
    helpful BOOLEAN,
    feedback_text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (query_id) REFERENCES query_logs(id) ON DELETE CASCADE
);

-- API configuration (admin dashboard)
CREATE TABLE api_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Use SERIAL for PostgreSQL
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

-- Usage statistics (daily aggregates)
CREATE TABLE usage_stats (
    date DATE PRIMARY KEY,
    total_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,
    avg_response_time DECIMAL(10,2),
    success_rate DECIMAL(5,2),
    top_products TEXT, -- JSON string
    unique_users INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0
);

-- Admin users for dashboard access
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Use SERIAL for PostgreSQL
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    login_attempts INTEGER DEFAULT 0,
    locked_until DATETIME
);

-- Cached responses for performance
CREATE TABLE response_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Use SERIAL for PostgreSQL
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    product VARCHAR(50) NOT NULL,
    response_text TEXT NOT NULL,
    confidence DECIMAL(3,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    hit_count INTEGER DEFAULT 0
);

-- System logs for monitoring
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Use SERIAL for PostgreSQL
    level VARCHAR(20) NOT NULL, -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    message TEXT NOT NULL,
    module VARCHAR(100),
    function_name VARCHAR(100),
    line_number INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    additional_data TEXT -- JSON string for extra context
);

-- Indexes for performance
CREATE INDEX idx_query_logs_timestamp ON query_logs(timestamp);
CREATE INDEX idx_query_logs_product ON query_logs(product);
CREATE INDEX idx_query_logs_success ON query_logs(success);
CREATE INDEX idx_query_logs_hash ON query_logs(query_hash);

CREATE INDEX idx_feedback_timestamp ON feedback(timestamp);
CREATE INDEX idx_feedback_helpful ON feedback(helpful);

CREATE INDEX idx_usage_stats_date ON usage_stats(date);

CREATE INDEX idx_response_cache_hash ON response_cache(query_hash);
CREATE INDEX idx_response_cache_product ON response_cache(product);
CREATE INDEX idx_response_cache_expires ON response_cache(expires_at);

CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX idx_system_logs_level ON system_logs(level);

-- Insert default configuration values
INSERT INTO api_config (config_key, config_value, description) VALUES
('claude_api_key', '', 'Claude API key for AI integration'),
('max_query_length', '2000', 'Maximum allowed query length in characters'),
('rate_limit_per_hour', '100', 'Maximum queries per hour per IP address'),
('enable_caching', 'true', 'Enable response caching for performance'),
('cache_expiry_hours', '24', 'Hours before cached responses expire'),
('enable_analytics', 'true', 'Enable usage analytics collection'),
('system_name', 'STRATUS Bug Advisor', 'System display name'),
('version', '1.0.0', 'Current system version'),
('maintenance_mode', 'false', 'Enable maintenance mode'),
('debug_mode', 'false', 'Enable debug logging');

-- Insert default admin user (password: 'admin123' - change in production!)
INSERT INTO admin_users (username, password_hash, email, is_active) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfBgRzgYvYv7EBG', 'admin@stratus.com', true);

-- Create triggers for automatic statistics updates (SQLite version)
-- Note: For PostgreSQL, use proper trigger functions

-- Trigger to update usage stats when queries are logged
CREATE TRIGGER update_usage_stats_after_query
AFTER INSERT ON query_logs
BEGIN
    INSERT OR REPLACE INTO usage_stats (
        date, 
        total_queries, 
        successful_queries,
        avg_response_time,
        success_rate
    )
    SELECT 
        DATE(NEW.timestamp) as date,
        COUNT(*) as total_queries,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_queries,
        AVG(response_time_ms) as avg_response_time,
        (CAST(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) * 100 as success_rate
    FROM query_logs 
    WHERE DATE(timestamp) = DATE(NEW.timestamp);
END;

-- Trigger to update cache hit count
CREATE TRIGGER update_cache_hit_count
AFTER UPDATE ON response_cache
WHEN NEW.hit_count > OLD.hit_count
BEGIN
    UPDATE response_cache 
    SET hit_count = NEW.hit_count 
    WHERE id = NEW.id;
END;
