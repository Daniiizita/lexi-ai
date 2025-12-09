"""
Celery tasks para processamento assíncrono de traduções.
"""

from celery import Celery
from typing import List
import os
import time
from pathlib import Path
import tempfile
from datetime import datetime

from .config import settings
from .router import get_translator
from .database import get_db
from .models import TranslationJob, TranslationChunk
from .logger import logger
from .infraestructure.storage.minio_client import get_minio_client

# Inicializa Celery
celery_app = Celery(
    "lexi_translator",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Configurações
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora max por task
    worker_prefetch_multiplier=1,  # Processa 1 task por vez (GPU limitada)
)


@celery_app.task(bind=True, name="translate_book")
def translate_book_task(
    self, 
    job_id: str, 
    minio_source_path: str,
    batch_size: int = 16
):
    """
    Task principal: traduz um livro completo em chunks.
    
    Args:
        job_id: UUID do job no banco
        minio_source_path: Caminho do arquivo no MinIO
        batch_size: Tamanho do batch para GPU
    """
    logger.info(f"[Task {self.request.id}] Iniciando job {job_id}")
    
    minio = get_minio_client()
    start_time = time.time()
    
    with get_db() as db:
        job = db.query(TranslationJob).filter_by(id=job_id).first()
        if not job:
            logger.error(f"Job {job_id} não encontrado")
            return {"error": "Job not found"}
        
        job.status = "processing"
        job.started_at = datetime.now()
        db.commit()
        
        try:
            # 1. Download do MinIO
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tmp_file:
                tmp_path = tmp_file.name
            
            logger.info(f"[Job {job_id}] Baixando de MinIO: {minio_source_path}")
            minio.download_file(minio_source_path, tmp_path)
            
            # 2. Lê conteúdo
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 3. Divide em chunks (com mais contexto)
            chunks = _split_into_chunks(content, max_tokens=512)
            job.total_chunks = len(chunks)
            db.commit()
            
            logger.info(f"[Job {job_id}] Total de chunks: {len(chunks)}")
            
            # 4. Cria chunks no banco
            db_chunks = []
            for idx, chunk_text in enumerate(chunks):
                chunk = TranslationChunk(
                    job_id=job_id,
                    chunk_index=idx,  # ← Mantém ordem
                    source_text=chunk_text,
                    status="pending"
                )
                db_chunks.append(chunk)
                db.add(chunk)
            db.commit()
            
            # 5. Traduz em batch
            translator = get_translator()
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_indices = list(range(i, min(i + batch_size, len(chunks))))
                
                logger.info(f"[Job {job_id}] Traduzindo batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
                
                translations = translator.translate_batch(batch, batch_size=batch_size)
                
                # ← CORRIGIDO: mapeia diretamente pelo chunk_index
                for chunk_idx, translation in zip(batch_indices, translations):
                    # Busca chunk correto pelo chunk_index
                    chunk = next(c for c in db_chunks if c.chunk_index == chunk_idx)
                    chunk.translated_text = translation
                    chunk.status = "completed"
                    chunk.completed_at = datetime.now()
                    
                    job.chunks_translated += 1
                
                db.commit()
                
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": job.chunks_translated,
                        "total": job.total_chunks,
                        "percent": int(job.chunks_translated / job.total_chunks * 100)
                    }
                )
            
            # 6. Monta arquivo final ORDENADO por chunk_index
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_translated.txt', encoding='utf-8') as out_file:
                out_path = out_file.name
                
                # ← CORRIGIDO: ordena chunks antes de escrever
                sorted_chunks = sorted(db_chunks, key=lambda c: c.chunk_index)
                
                for chunk in sorted_chunks:
                    out_file.write(chunk.translated_text + "\n\n")
            
            # 7. Upload para MinIO
            minio_output_path = minio_source_path.replace(".txt", "_translated.txt")
            minio_url = minio.upload_file(out_path, minio_output_path)
            
            job.translated_path = minio_url
            
            # 8. Limpa temporários
            os.unlink(tmp_path)
            os.unlink(out_path)
            
            # 9. Finaliza job
            job.status = "completed"
            job.completed_at = datetime.now()
            job.translation_time_seconds = time.time() - start_time
            db.commit()
            
            logger.info(f"[Job {job_id}] ✅ Concluído em {job.translation_time_seconds:.2f}s | MinIO: {minio_url}")
            
            return {
                "status": "success",
                "job_id": job_id,
                "chunks_translated": job.chunks_translated,
                "time_seconds": job.translation_time_seconds,
                "translated_url": minio_url
            }
            
        except Exception as e:
            logger.error(f"[Job {job_id}] ❌ Erro: {e}", exc_info=True)
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            raise


def _split_into_chunks(text: str, max_tokens: int = 512) -> List[str]:
    """
    Divide texto em chunks com overlap para manter contexto.
    
    TODO: Melhorar com tokenização real do modelo
    """
    # Split em parágrafos primeiro (melhor quebra semântica)
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        words = para.split()
        para_length = len(words)
        
        if current_length + para_length <= max_tokens:
            # Adiciona parágrafo ao chunk atual
            current_chunk.append(para)
            current_length += para_length
        else:
            # Salva chunk atual se não estiver vazio
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            
            # Inicia novo chunk com parágrafo atual
            if para_length > max_tokens:
                # Parágrafo muito grande: divide em sentenças
                sentences = para.split('. ')
                temp_chunk = []
                temp_length = 0
                
                for sent in sentences:
                    sent_words = sent.split()
                    if temp_length + len(sent_words) <= max_tokens:
                        temp_chunk.append(sent)
                        temp_length += len(sent_words)
                    else:
                        if temp_chunk:
                            chunks.append('. '.join(temp_chunk) + '.')
                        temp_chunk = [sent]
                        temp_length = len(sent_words)
                
                if temp_chunk:
                    chunks.append('. '.join(temp_chunk) + '.')
                
                current_chunk = []
                current_length = 0
            else:
                current_chunk = [para]
                current_length = para_length
    
    # Adiciona último chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


@celery_app.task(name="health_check")
def health_check_task():
    """Task simples para health check"""
    return {"status": "ok", "timestamp": time.time()}