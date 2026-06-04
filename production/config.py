from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 2222
    
    # vLLM
    VLLM_BASE_URL: str = "http://localhost:1111"
    MODEL_NAME: str = "qwen3.6-moe"
    MAX_TOKENS: int = 4096
    
    # MySQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "avaniko_llm"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    
    # Security
    API_KEY_PREFIX: str = "sk-ava-"
    ADMIN_EMAIL: str = "karthick.murugan@avaniko.com"
    ADMIN_PASSWORD: str = "Avan@2025"
    
    # Chunking
    MAX_CHUNK_TOKENS: int = 4000
    MAX_DIRECT_TOKENS: int = 2000
    
    # Storage
    UPLOAD_DIR: str = "/workspace/production/uploads"
    LOG_DIR: str = "/workspace/production/logs"
    
    # RAG
    VECTOR_DB_PATH: str = "/workspace/production/vectordb"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = "/workspace/.env"
        extra = "allow"

@lru_cache()
def get_settings():
    return Settings()
