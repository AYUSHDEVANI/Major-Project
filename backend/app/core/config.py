import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pydantic import field_validator

# Explicitly load .env from project root
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Modal Vision-Language RAG"
    API_V1_STR: str = "/api/v1"
    
    # Qdrant Config
    QDRANT_MODE: str = "local"
    QDRANT_PATH: str = "local_qdrant_db"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    @property
    def QDRANT_URL(self) -> str:
        if self.QDRANT_MODE == "server":
            return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
        return "" # Not used in local mode
    COLLECTION_NAME: str = "manuals"
    
    # Model Config
    # using ViT-B-32 for decent balance of speed/performance
    # Upgrade path: ViT-L-14 + datacomp_xl_s13b_b90k (768-dim, better accuracy)
    OPENCLIP_MODEL_NAME: str = "ViT-B-32" 
    OPENCLIP_PRETRAINED: str = "laion2b_s34b_b79k"
    
    # Embedding dimension lookup (must match the CLIP model)
    _CLIP_DIMS = {"ViT-B-32": 512, "ViT-B-16": 512, "ViT-L-14": 768, "ViT-H-14": 1024}
    
    @property
    def EMBEDDING_DIM(self) -> int:
        return self._CLIP_DIMS.get(self.OPENCLIP_MODEL_NAME, 512)
    
    # Agent Config
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    @field_validator("GOOGLE_API_KEY", "GROQ_API_KEY")
    @classmethod
    def check_api_keys(cls, v: str, info) -> str:
        if not v or "your_key_here" in v:
            raise ValueError(f"{info.field_name} must be set and cannot be a placeholder.")
        return v

    class Config:
        env_file = ".env"

settings = Settings()
