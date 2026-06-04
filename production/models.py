from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum

# ── Enums ────────────────────────────────────────────────
class ChatMode(str, Enum):
    chat     = "chat"
    reason   = "reason"
    code     = "code"
    summarize = "summarize"
    translate = "translate"

class DocType(str, Enum):
    invoice  = "invoice"
    receipt  = "receipt"
    id_card  = "id_card"
    contract = "contract"
    resume   = "resume"
    auto     = "auto"

class FileType(str, Enum):
    pdf      = "pdf"
    image    = "image"
    word     = "word"
    excel    = "excel"
    audio    = "audio"
    text     = "text"
    auto     = "auto"

# ── Request Models ───────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    mode: ChatMode = ChatMode.chat
    session_id: Optional[str] = None
    stream: bool = False
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=16000)
    system_prompt: Optional[str] = None
    project_id: Optional[str] = None

class OCRRequest(BaseModel):
    image_base64: str
    doc_type: DocType = DocType.auto
    extract_tables: bool = True
    output_format: str = "json"

class FileRequest(BaseModel):
    doc_type: DocType = DocType.auto
    mode: ChatMode = ChatMode.chat
    question: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = False
    chunk_size: int = Field(default=4000, ge=500, le=8000)

class RAGRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)
    stream: bool = False

class EmbedRequest(BaseModel):
    texts: List[str]
    doc_id: Optional[str] = None

class RegisterRequest(BaseModel):
    user_name: str
    user_email: str
    daily_limit: int = Field(default=1000, ge=1, le=100000)

# ── Project Models ────────────────────────────────────────
class ProjectCreate(BaseModel):
    name: str
    system_prompt: str
    description: Optional[str] = ""
    model: str = "qwen3.6-moe"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=16000)

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

# ── OpenAI-Compatible Models ─────────────────────────────
class OpenAIMessage(BaseModel):
    role: str
    content: str

class OpenAIChatRequest(BaseModel):
    model: str = "qwen3.6-moe"
    messages: List[OpenAIMessage]
    stream: bool = False
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=16000)
    project_id: Optional[str] = None

# ── Response Models ──────────────────────────────────────
class ChatResponse(BaseModel):
    response: str
    mode: str
    session_id: Optional[str] = None
    tokens_used: int = 0
    response_time_ms: int = 0

class OCRResponse(BaseModel):
    status: str
    data: Any
    doc_type: str
    pages_processed: int = 1
    response_time_ms: int = 0

class FileResponse(BaseModel):
    status: str
    response: str
    file_type: str
    chunks_processed: int = 0
    tokens_used: int = 0
    response_time_ms: int = 0

class RegisterResponse(BaseModel):
    api_key: str
    user_name: str
    user_email: str
    daily_limit: int
    message: str = "API Key generated successfully"

class HealthResponse(BaseModel):
    gateway: str
    vllm: str
    database: str
    version: str = "1.0.0"

class UsageResponse(BaseModel):
    total_requests: int
    total_tokens: int
    avg_response_ms: float
    requests_today: int
    daily_limit: int
