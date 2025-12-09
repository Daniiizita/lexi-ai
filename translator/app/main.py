from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Optional, List
from contextlib import asynccontextmanager
import uuid
import os

from starlette.types import Lifespan

from .schemas import (
    TranslationRequest, 
    TranslationResponse,
    ChunkInput,
    ChunkOutput
)
from .router import get_translator
from .config import settings
from .tasks import translate_book_task, health_check_task
from .infraestructure.storage.minio_client import get_minio_client


# -------------------- LIFESPAN CORRETO --------------------
@asynccontextmanager
async def lifespan(app: FastAPI):

    # ----------- STARTUP -----------
    print("\n" + "="*50)
    print("🚀 LEXI Translator API Iniciando...")
    print("="*50)
    print(settings)
    print("="*50 + "\n")

    print("⏳ Pre-carregando modelo de tradução...")
    get_translator()
    print("✅ Modelo pré-carregado e pronto para uso!\n")

    yield   # Aqui a aplicação começa a rodar

    # ----------- SHUTDOWN ----------
    print("🛑 Encerrando LEXI Translator API...")

# -------------------- FASTAPI APP --------------------

app = FastAPI(
    title="LEXI Translator API",
    version="1.0.0",
    description="API de tradução literária EN→PT usando modelos open-source",
    lifespan=lifespan
)

# -------------------- ROTAS --------------------
@app.get("/health")
def health():
    """Healthcheck para Kubernetes/Docker"""
    return {
        "status": "ok",
        "environment": settings.environment,
        "model_provider": settings.model_provider,
        "model_name": settings.model_name,
        "storage": settings.storage_dir
    }


@app.post("/translate", response_model=ChunkOutput)
def translate_chunk(chunk: ChunkInput):
    """
    Tradução profissional por chunks conforme especificação LEXI.
    
    Segue os princípios:
    - Fidelidade ao sentido e tom
    - Coerência terminológica (usa glossário)
    - Preservação de formatação HTML inline
    """
    translator = get_translator()  # Reutiliza instância carregada
    
    # Monta contexto completo
    full_text = f"{chunk.context_before} {chunk.plain_text} {chunk.context_after}".strip()
    
    translated = translator.translate(full_text)
    
    return ChunkOutput(
        chunk_id=chunk.chunk_id,
        translated_html=translated,
        decisions=[],
        terms_used=[],
        flags=[]
    )


@app.post("/translate/sync", response_model=TranslationResponse)
def translate_sync(req: TranslationRequest):
    """Tradução síncrona simples para testes rápidos"""
    if not req.text or len(req.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Texto vazio")
    
    job_id = str(uuid.uuid4())
    
    translator = get_translator()  # Reutiliza instância carregada
    translated = translator.translate(req.text)
    
    # Salva resultado
    out_path = os.path.join(settings.storage_dir, f"{job_id}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(translated)
    
    return TranslationResponse(job_id=job_id, translated=translated)


@app.post("/translate/upload")
async def translate_upload(
    file: UploadFile = File(...), 
    target_lang: Optional[str] = "pt"
):
    """Upload de arquivo para tradução assíncrona via worker"""
    job_id = str(uuid.uuid4())
    filename = f"{job_id}_{file.filename}"
    save_path = os.path.join(settings.storage_dir, filename)
    
    # Salva arquivo
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Cria flag para o worker processar
    pending_flag = save_path + ".pending"
    with open(pending_flag, "w") as f:
        f.write(target_lang) # pyright: ignore[reportArgumentType]
    
    return {
        "job_id": job_id,
        "filename": filename,
        "status": "pending"
    }


@app.post("/translate/async")
async def translate_async(file: UploadFile = File(...)):
    """
    Upload de arquivo para tradução assíncrona via Celery + MinIO.
    
    Flow:
    1. Upload para MinIO
    2. Cria job no PostgreSQL
    3. Enfileira task no Celery/Redis
    """
    from .models import TranslationJob
    from .database import get_db
    
    job_id = str(uuid.uuid4())
    
    # 1. Upload para MinIO
    minio = get_minio_client()
    minio_path = f"jobs/{job_id}/source_{file.filename}"
    
    file_content = await file.read()
    minio_url = minio.upload_bytes(
        file_content,
        minio_path,
        content_type=file.content_type or "application/octet-stream"
    )
    
    # 2. Cria job no banco
    with get_db() as db:
        job = TranslationJob(
            id=job_id,
            filename=file.filename or "unknown.txt",
            file_size=len(file_content),
            status="queued",
            source_path=minio_url,
            model_name=settings.model_name
        )
        db.add(job)
        db.commit()
    
    # 3. Enfileira task no Celery
    task = translate_book_task.delay(job_id, minio_path)
    
    return {
        "job_id": job_id,
        "task_id": task.id,
        "status": "queued",
        "message": "Arquivo enviado para MinIO. Use /status/{job_id} para acompanhar.",
        "minio_url": minio_url
    }


@app.get("/status/{job_id}")
def get_status(job_id: str):
    """Consulta status de um job de tradução"""
    from .database import get_db
    from .models import TranslationJob
    
    with get_db() as db:
        job = db.query(TranslationJob).filter_by(id=job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        
        return job.to_dict()


@app.get("/health/celery")
def health_celery():
    """Verifica se o Celery Worker está ativo"""
    try:
        result = health_check_task.delay()
        response = result.get(timeout=5)
        return {"status": "ok", "worker_response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/health/minio")
def health_minio():
    """Verifica conectividade com MinIO"""
    try:
        minio = get_minio_client()
        
        # Tenta listar um unico objeto
        files = minio.list_files(prefix="", max_results=1)
        
        return {
            "status": "ok",
            "bucket": minio.bucket,
            "endpoint": settings.minio_endpoint,
            "accessible": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "accessible": False
        }


@app.post("/translate/batch", response_model=List[ChunkOutput])
def translate_batch(chunks: List[ChunkInput]):
    """
    Tradução em batch (até 5x mais rápido que individual).
    Processa múltiplos chunks de uma vez.
    """
    translator = get_translator()
    
    # Prepara textos
    texts = [
        f"{c.context_before} {c.plain_text} {c.context_after}".strip() 
        for c in chunks
    ]
    
    # Traduz em batch
    translations = translator.translate_batch(texts)
    
    # Monta respostas
    outputs = []
    for chunk, translated in zip(chunks, translations):
        outputs.append(ChunkOutput(
            chunk_id=chunk.chunk_id,
            translated_html=translated,
            decisions=[],
            terms_used=[],
            flags=[]
        ))
    
    return outputs