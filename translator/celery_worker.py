"""
Celery Worker entrypoint.

Executa tasks de tradução em background com GPU.

Uso:
    celery -A celery_worker worker --loglevel=info --concurrency=1
"""

from app.tasks import celery_app
from app.config import settings
from app.logger import logger

if __name__ == "__main__":
    logger.info(f"🚀 Iniciando Celery Worker")
    logger.info(f"📡 Redis: {settings.redis_url}")
    logger.info(f"🗄️ Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'N/A'}")
    
    celery_app.start()