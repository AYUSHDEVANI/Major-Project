import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Explicitly load .env from project root
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multi-Modal Vision-Language RAG"
    API_V1_STR: str = "/api/v1"
    
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
    OPENCLIP_MODEL_NAME: str = "ViT-B-32" 
    OPENCLIP_PRETRAINED: str = "laion2b_s34b_b79k"
    
    # Agent Config
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()
