"""Configuration Management for ALO System"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

@dataclass
class TelegramConfig:
    bot_token: str
    admin_id: int

@dataclass
class LLMConfig:
    provider: str  # anthropic, openai, local
    api_key: Optional[str]
    model: str
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7

@dataclass
class RAGConfig:
    vector_db_path: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    similarity_threshold: float = 0.7
    max_results: int = 5

@dataclass
class LearningConfig:
    memory_path: str
    auto_learn: bool
    reflection_enabled: bool
    confidence_threshold: float = 0.6

@dataclass
class ExecutionConfig:
    max_iterations: int
    code_execution_enabled: bool
    safe_mode: bool
    workspace_path: str
    timeout: int = 300
    max_file_size: int = 10485760  # 10MB

class Config:
    def __init__(self):
        self.telegram = TelegramConfig(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            admin_id=int(os.getenv("TELEGRAM_ADMIN_ID", "0"))
        )

        self.llm = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("OPENAI_API_KEY"),
            # CORRECTED LINE: Using default value properly
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("LLM_BASE_URL")
        )

        self.rag = RAGConfig(
            vector_db_path=os.getenv("VECTOR_DB_PATH", "./data/vectordb"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "512")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50"))
        )

        self.learning = LearningConfig(
            memory_path=os.getenv("MEMORY_PATH", "./data/memory"),
            auto_learn=os.getenv("AUTO_LEARN", "true").lower() == "true",
            reflection_enabled=os.getenv("REFLECTION_ENABLED", "true").lower() == "true"
        )

        self.execution = ExecutionConfig(
            max_iterations=int(os.getenv("MAX_ITERATIONS", "10")),
            code_execution_enabled=os.getenv("CODE_EXECUTION_ENABLED", "true").lower() == "true",
            safe_mode=os.getenv("SAFE_MODE", "false").lower() == "true",
            workspace_path=os.getenv("WORKSPACE_PATH", "./workspace")
        )

        self._validate()

    def _validate(self):
        """Validate critical configuration"""
        if not self.telegram.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        if not self.telegram.admin_id:
            raise ValueError("TELEGRAM_ADMIN_ID not set")
        # Ensure LLM API key is present for providers that require it
        if self.llm.provider in ["anthropic", "openai"] and not self.llm.api_key:
            raise ValueError(f"LLM_API_KEY (OPENAI_API_KEY) required for {self.llm.provider}")

        # Create directories if they don't exist
        os.makedirs(self.rag.vector_db_path, exist_ok=True)
        os.makedirs(self.learning.memory_path, exist_ok=True)
        os.makedirs(self.execution.workspace_path, exist_ok=True)
        os.makedirs("./logs", exist_ok=True)

# Global configuration instance
config = Config()

