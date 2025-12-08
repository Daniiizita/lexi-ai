import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """Configurações centralizadas da aplicação"""
    
    def __init__(self):
        # Detecta ambiente
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Carrega .env apropriado
        env_file = Path(__file__).parent.parent / f".env.{self.environment}"
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Carregado: {env_file}")
        else:
            print(f"⚠️ Arquivo não encontrado: {env_file}")
        
        # Hugging Face
        self.hf_token: Optional[str] = os.getenv("HF_TOKEN")
        self.model_name: str = os.getenv("MODEL_NAME", "Helsinki-NLP/opus-mt-en-pt")
        self.model_provider: str = os.getenv("MODEL_PROVIDER", "HF")
        
        # Storage
        self.storage_dir: str = os.getenv("STORAGE_DIR", "./storage")
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        
        # API
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.api_reload: bool = os.getenv("API_RELOAD", "false").lower() == "true"
        
        # Logs
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    def __repr__(self):
        return f"""Settings(
    environment={self.environment},
    model_name={self.model_name},
    storage_dir={self.storage_dir},
    hf_token={'***' if self.hf_token else None}
)"""


# Instância global
settings = Settings()