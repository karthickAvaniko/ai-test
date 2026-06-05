from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, Integer, BigInteger, Float, DateTime, Text, ARRAY, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
import uuid
from config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
    connect_args={"ssl": False}  # Disable SSL for local dev on Windows
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

# ── ORM Models ────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email      = Column(String(255), unique=True, nullable=False)
    name       = Column(String(255), nullable=False)
    password   = Column(String(255), nullable=False)
    role       = Column(String(20), default="user")
    is_active  = Column(Boolean, default=True)
    is_verified= Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class APIKey(Base):
    __tablename__ = "api_keys"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), nullable=False)
    key_hash         = Column(String(64), unique=True, nullable=False)
    key_prefix       = Column(String(20), nullable=False)
    name             = Column(String(100), default="Default Key")
    is_active        = Column(Boolean, default=True)
    daily_limit      = Column(Integer, default=1000)
    monthly_limit    = Column(Integer, default=30000)
    requests_today   = Column(Integer, default=0)
    requests_month   = Column(Integer, default=0)
    total_requests   = Column(Integer, default=0)
    total_tokens     = Column(BigInteger, default=0)
    last_used_at     = Column(DateTime(timezone=True))
    expires_at       = Column(DateTime(timezone=True))
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

class AIModel(Base):
    __tablename__ = "models"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id       = Column(String(100), unique=True, nullable=False)
    name           = Column(String(200), nullable=False)
    provider       = Column(String(50), nullable=False)
    provider_url   = Column(Text)
    provider_key   = Column(Text)
    context_length = Column(Integer, default=32768)
    input_cost     = Column(DECIMAL(10, 6), default=0)
    output_cost    = Column(DECIMAL(10, 6), default=0)
    is_active      = Column(Boolean, default=True)
    capabilities   = Column(ARRAY(String), default=["chat"])
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

class UsageLog(Base):
    __tablename__ = "usage_logs"
    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id        = Column(UUID(as_uuid=True))
    user_id           = Column(UUID(as_uuid=True))
    model_id          = Column(String(100))
    endpoint          = Column(String(200), nullable=False)
    prompt_tokens     = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens      = Column(Integer, default=0)
    response_time_ms  = Column(Integer, default=0)
    status_code       = Column(Integer, default=200)
    status            = Column(String(20), default="success")
    cost              = Column(DECIMAL(10, 6), default=0)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

class RequestLog(Base):
    __tablename__ = "request_logs"
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id      = Column(UUID(as_uuid=True))
    user_id         = Column(UUID(as_uuid=True))
    method          = Column(String(10), nullable=False)
    endpoint        = Column(String(200), nullable=False)
    request_body    = Column(JSONB)
    response_status = Column(Integer)
    response_time_ms= Column(Integer)
    ip_address      = Column(INET)
    user_agent      = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

class Project(Base):
    __tablename__ = "projects"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), nullable=False)
    project_id    = Column(String(60), unique=True, nullable=False)
    name          = Column(String(200), nullable=False)
    description   = Column(Text, default="")
    system_prompt = Column(Text, nullable=False)
    model_id      = Column(String(100), default="qwen3-moe")
    temperature   = Column(Float, default=0.7)
    max_tokens    = Column(Integer, default=4096)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Billing(Base):
    __tablename__ = "billing"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), nullable=False)
    period_start   = Column(DateTime(timezone=True))
    period_end     = Column(DateTime(timezone=True))
    total_tokens   = Column(BigInteger, default=0)
    total_requests = Column(Integer, default=0)
    total_cost     = Column(DECIMAL(10, 4), default=0)
    status         = Column(String(20), default="pending")
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

# ── DB Session dependency ─────────────────────────────────
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Create all tables — safe for multi-worker startup (checkfirst=True)."""
    try:
        async with engine.begin() as conn:
            # checkfirst=True prevents errors if tables already exist
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    except Exception as e:
        # Race condition on multi-worker startup — tables already created by another worker
        if "already exists" in str(e) or "duplicate" in str(e).lower():
            pass  # Tables exist, that's fine
        else:
            raise
