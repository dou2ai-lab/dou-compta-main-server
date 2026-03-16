# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Configuration for RAG service
# -----------------------------------------------------------------------------

"""
Configuration for RAG Service
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "rag-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, good quality
    EMBEDDING_DIMENSION: int = 384  # Dimension for all-MiniLM-L6-v2
    EMBEDDING_DEVICE: str = "cpu"  # cpu or cuda
    
    # LLM Provider (for explanations)
    LLM_PROVIDER: str = "gemini"  # gemini, openai, anthropic
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "models/gemini-2.0-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: str = ""
    
    # RAG Settings
    TOP_K_RESULTS: int = 5  # Number of relevant documents to retrieve
    SIMILARITY_THRESHOLD: float = 0.4  # Minimum similarity score (0.4 so "What is the expense policy?" etc. return policy chunks)
    
    # Chunking
    CHUNK_SIZE: int = 500  # Characters per chunk
    CHUNK_OVERLAP: int = 50  # Overlap between chunks
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

settings = Settings()

