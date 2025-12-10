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
        self.model_name: str = os.getenv("MODEL_NAME", "Helsinki-NLP/opus-mt-tc-big-en-pt")
        self.model_provider: str = os.getenv("MODEL_PROVIDER", "HF")
        
        # Database
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/lexi_db"
        )
        
        # Redis/Celery
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # MinIO/S3
        self.minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "change_me_please")
        self.minio_bucket: str = os.getenv("MINIO_BUCKET", "lexi-translations")
        
        # Storage
        self.storage_dir: str = os.getenv("STORAGE_DIR", "/data" if os.path.exists("/data") else "./storage")
        
        # Cria diretório se não existir
        try:
            Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
            print(f"✅ Storage criado/verificado: {self.storage_dir}")
        except PermissionError:
            print(f"⚠️ Sem permissão para criar {self.storage_dir} (usando existente)")
        
        # API
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        
        # Logs
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    def __repr__(self):
        return f"""Settings(
    environment={self.environment},
    model_name={self.model_name},
    storage_dir={self.storage_dir},
    database_url={self.database_url.split('@')[1] if '@' in self.database_url else 'N/A'},
    redis_url={self.redis_url},
    log_level={self.log_level}
)"""


# Instância global
settings = Settings()