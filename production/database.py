import pymysql
import secrets
import hashlib
from datetime import datetime
from config import get_settings

settings = get_settings()

def get_db():
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

# ── DB Init (idempotent — run on startup) ───────────────
def init_db():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    api_key VARCHAR(100) UNIQUE NOT NULL,
                    user_name VARCHAR(100) NOT NULL,
                    user_email VARCHAR(200) UNIQUE NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    requests_today INT DEFAULT 0,
                    total_requests INT DEFAULT 0,
                    daily_limit INT DEFAULT 1000,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    project_id VARCHAR(60) UNIQUE NOT NULL,
                    api_key VARCHAR(100) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT DEFAULT '',
                    system_prompt TEXT NOT NULL,
                    model VARCHAR(100) DEFAULT 'qwen3.6-moe',
                    temperature FLOAT DEFAULT 0.7,
                    max_tokens INT DEFAULT 4096,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_proj_api_key (api_key)
                ) CHARACTER SET utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    api_key VARCHAR(100) NOT NULL,
                    session_id VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    tokens_used INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session (session_id),
                    INDEX idx_hist_api_key (api_key)
                ) CHARACTER SET utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    api_key VARCHAR(100) NOT NULL,
                    endpoint VARCHAR(200) NOT NULL,
                    file_type VARCHAR(50) DEFAULT '',
                    tokens_used INT DEFAULT 0,
                    response_time_ms INT DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'success',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_log_api_key (api_key)
                ) CHARACTER SET utf8mb4
            """)
        print("✅ DB tables ready")
    finally:
        db.close()

# ── Project Operations ───────────────────────────────────
def create_project(api_key: str, name: str, system_prompt: str,
                   description: str = "", model: str = "qwen3.6-moe",
                   temperature: float = 0.7, max_tokens: int = 4096) -> str:
    project_id = "proj-" + secrets.token_urlsafe(16)
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO projects
                (project_id, api_key, name, description, system_prompt, model, temperature, max_tokens)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (project_id, api_key, name, description, system_prompt, model, temperature, max_tokens))
        return project_id
    finally:
        db.close()

def get_project(project_id: str, api_key: str) -> dict | None:
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT * FROM projects
                WHERE project_id = %s AND api_key = %s AND is_active = TRUE
            """, (project_id, api_key))
            return cur.fetchone()
    finally:
        db.close()

def list_projects(api_key: str) -> list:
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT project_id, name, description, model,
                       temperature, max_tokens, created_at, updated_at
                FROM projects
                WHERE api_key = %s AND is_active = TRUE
                ORDER BY created_at DESC
            """, (api_key,))
            return cur.fetchall()
    finally:
        db.close()

def update_project(project_id: str, api_key: str, **kwargs) -> bool:
    allowed = {"name", "description", "system_prompt", "model", "temperature", "max_tokens"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return False
    db = get_db()
    try:
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [project_id, api_key]
        with db.cursor() as cur:
            cur.execute(
                f"UPDATE projects SET {set_clause} WHERE project_id = %s AND api_key = %s",
                values
            )
        return True
    finally:
        db.close()

def delete_project(project_id: str, api_key: str) -> bool:
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                UPDATE projects SET is_active = FALSE
                WHERE project_id = %s AND api_key = %s
            """, (project_id, api_key))
        return True
    finally:
        db.close()

# ── API Key Operations ───────────────────────────────────
def generate_api_key(user_name: str, user_email: str, daily_limit: int = 1000) -> str:
    api_key = settings.API_KEY_PREFIX + secrets.token_urlsafe(32)
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO api_keys 
                (api_key, user_name, user_email, daily_limit)
                VALUES (%s, %s, %s, %s)
            """, (api_key, user_name, user_email, daily_limit))
        return api_key
    finally:
        db.close()

def validate_api_key(api_key: str) -> dict | None:
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT * FROM api_keys 
                WHERE api_key = %s 
                AND is_active = TRUE
            """, (api_key,))
            row = cur.fetchone()
            if not row:
                return None
            # Rate limit check
            if row["requests_today"] >= row["daily_limit"]:
                return None
            # Increment counter
            cur.execute("""
                UPDATE api_keys 
                SET requests_today = requests_today + 1,
                    total_requests = total_requests + 1
                WHERE api_key = %s
            """, (api_key,))
            return row
    finally:
        db.close()

def reset_daily_counts():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("UPDATE api_keys SET requests_today = 0")
    finally:
        db.close()

# ── Chat History Operations ──────────────────────────────
def save_message(api_key: str, session_id: str, role: str, 
                 content: str, tokens_used: int = 0):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_history 
                (api_key, session_id, role, content, tokens_used)
                VALUES (%s, %s, %s, %s, %s)
            """, (api_key, session_id, role, content, tokens_used))
    finally:
        db.close()

def get_history(session_id: str, limit: int = 20) -> list:
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT role, content FROM chat_history
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (session_id, limit))
            rows = cur.fetchall()
            return list(reversed(rows))
    finally:
        db.close()

def clear_history(session_id: str):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                DELETE FROM chat_history 
                WHERE session_id = %s
            """, (session_id,))
    finally:
        db.close()

# ── Usage Log Operations ─────────────────────────────────
def log_usage(api_key: str, endpoint: str, file_type: str,
              tokens_used: int, response_time_ms: int, status: str):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO usage_logs
                (api_key, endpoint, file_type, tokens_used, 
                 response_time_ms, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (api_key, endpoint, file_type, 
                  tokens_used, response_time_ms, status))
    finally:
        db.close()

def get_usage_stats(api_key: str) -> dict:
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(tokens_used) as total_tokens,
                    AVG(response_time_ms) as avg_response_ms
                FROM usage_logs
                WHERE api_key = %s
            """, (api_key,))
            return cur.fetchone()
    finally:
        db.close()
