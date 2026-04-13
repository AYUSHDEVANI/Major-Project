import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pydantic import field_validator
from typing import Optional

# Explicitly load .env from project root
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Modal Vision-Language RAG"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./maintenance.db"
    
    # Qdrant Config
    QDRANT_MODE: str = "local" # local, server, or cloud
    QDRANT_PATH: str = "local_qdrant_db"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    
    COLLECTION_NAME: str = "manuals_v3" # Updated for Local MiniLM Embeddings
    
    # Model Config
    # Now using Local MiniLM (384-dim) - Tiny (80MB), stable, and region-independent
    EMBEDDING_DIM: int = 384
    
    # Agent Config
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")


    @field_validator("GOOGLE_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY")
    @classmethod
    def check_api_keys(cls, v: str, info) -> str:
        if not v or "your_key_here" in v:
            raise ValueError(f"{info.field_name} must be set and cannot be a placeholder.")
        return v

    class Config:
        env_file = ".env"

settings = Settings()
