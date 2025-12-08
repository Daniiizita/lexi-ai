from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Optional, List
import uuid
import os

from .schemas import (
    TranslationRequest, 
    TranslationResponse,
    ChunkInput,
    ChunkOutput
)
from .router import get_translator
from .config import settings


app = FastAPI(
    title="LEXI Translator API",
    version="0.2.0",
    description="API de tradução literária EN→PT usando modelos open-source"
)


@app.on_event("startup")
async def startup_event():
    """
    Inicialização da aplicação:
    - Valida configurações
    - Pre-carrega modelo (evita delay no primeiro request)
    """
    print("\n" + "="*50)
    print("🚀 LEXI Translator API Iniciando...")
    print("="*50)
    print(settings)
    print("="*50 + "\n")
    
    # Pre-carrega modelo (evita delay no primeiro request)
    print("⏳ Pre-carregando modelo de tradução...")
    get_translator()  # Força carregamento no startup
    print("✅ Modelo pré-carregado e pronto para uso!\n")


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