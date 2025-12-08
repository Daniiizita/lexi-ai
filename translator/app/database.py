from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .config import settings
from .models import Base

# Engine global
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.log_level == "DEBUG"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Cria todas as tabelas no startup"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


@contextmanager
def get_db() -> Session:
    """Context manager para sessões de DB"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """Dependency injection para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()