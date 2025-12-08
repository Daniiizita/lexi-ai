# LEXI-AI — Projeto completo (Protótipo → Produção)

> Repositório padrão de mercado para o projeto **LEXI-AI** — tradução de livros (EN → PT) usando modelos open‑source. Projetado para começar como protótipo local (Streamlit + FastAPI + Helsinki‑NLP) e evoluir para produção (containers, worker, storage, k8s, observability).

---

## Estrutura do repositório

``` plaintext

lexi-ai/
├─ frontend/                # Streamlit app
│  ├─ Dockerfile
│  └─ app.py
├─ translator/              # FastAPI + worker + modelos
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ app/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ translate.py
│     ├─ worker.py
│     └─ schemas.py
├─ infra/
│  ├─ docker-compose.yml
│  ├─ k8s-deployment.yaml
│  └─ k8s-hpa.yaml
├─ .github/workflows/ci.yml
└─ README.md
```

---

## Arquivos principais (conteúdo abaixo — copie para seus arquivos no repo)

> **ATENÇÃO:** por questões de direitos autorais, o sistema só processa arquivos que o usuário enviar — o projeto assume que o usuário fará upload dos livros.

### `README.md`

``` plaintext
# LEXI-AI

Projeto protótipo para tradução de livros (EN → PT) usando modelos open-source.

## Rodando localmente (dev)

1. Build e up com docker-compose:

   cd infra
   docker-compose up --build

2. Acesse Streamlit: http://localhost:8501
3. Acesse FastAPI docs: http://localhost:8000/docs
```

---

### `translator/requirements.txt`

``` plaintext
fastapi
uvicorn[standard]
transformers
sentencepiece
pydantic
python-multipart
```

---

### `translator/Dockerfile`

``` plaintext
FROM python:3.11-slim

RUN useradd -m appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app

RUN mkdir -p /data && chown appuser /data
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### `translator/app/__init__.py`

```python
# Pacote translator.app
```

---

### `translator/app/schemas.py`

```python
from pydantic import BaseModel
from typing import Optional

class TranslationRequest(BaseModel):
    text: str

class TranslationResponse(BaseModel):
    job_id: str
    translated: Optional[str]
```

---

### `translator/app/translate.py`

```python
from transformers import pipeline

# Carregamento lazy: a importação do módulo inicia o pipeline
# Em ambiente com memória limitada você pode carregar no evento startup do FastAPI
translator = pipeline("translation_en_to_pt", model="Helsinki-NLP/opus-mt-en-pt")


def translate_text_sync(text: str) -> str:
    """Traduz um bloco de texto. Para textos maiores, faça chunking antes."""
    # O pipeline pode dividir internamente; cuidado com tokens muito grandes
    res = translator(text)
    return res[0]["translation_text"]
```

---

### `translator/app/main.py`

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import os
from .translate import translate_text_sync
from .schemas import TranslationRequest, TranslationResponse

app = FastAPI(title="LEXI Translator API", version="0.1.0")

STORAGE_DIR = os.environ.get("STORAGE_DIR", "/data")
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/translate/sync", response_model=TranslationResponse)
def translate_sync(req: TranslationRequest):
    if not req.text or len(req.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Texto vazio")
    job_id = str(uuid.uuid4())
    translated = translate_text_sync(req.text)
    out_path = os.path.join(STORAGE_DIR, f"{job_id}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(translated)
    return TranslationResponse(job_id=job_id, translated=translated)

@app.post("/translate/upload")
async def translate_upload(file: UploadFile = File(...), target_lang: Optional[str] = "pt"):
    job_id = str(uuid.uuid4())
    filename = f"{job_id}_{file.filename}"
    save_path = os.path.join(STORAGE_DIR, filename)
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)
    pending_flag = save_path + ".pending"
    with open(pending_flag, "w") as f:
        f.write(target_lang)
    return {"job_id": job_id, "filename": filename}
```

---

### `translator/app/worker.py`

```python
import time, os, glob
from .translate import translate_text_sync

STORAGE_DIR = os.environ.get("STORAGE_DIR", "/data")

def process_pending_jobs():
    while True:
        pendings = glob.glob(os.path.join(STORAGE_DIR, "*.pending"))
        for p in pendings:
            try:
                original = p[:-8]
                target_lang = open(p).read().strip()
                # Suporte básico: assume txt; para pdf/epub, use loaders (pypdf, ebooklib)
                with open(original, "r", encoding="utf-8") as f:
                    content = f.read()
                translated = translate_text_sync(content)
                out_path = original + f".{target_lang}.translated.txt"
                with open(out_path, "w", encoding="utf-8") as out:
                    out.write(translated)
                os.remove(p)
            except Exception as e:
                print({"error": str(e), "job": p})
        time.sleep(5)

if __name__ == "__main__":
    process_pending_jobs()
```

---

### `frontend/Dockerfile`

``` dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### `frontend/requirements.txt`

``` plaintext
streamlit
requests
```

---

### `frontend/app.py`

```python
import streamlit as st
import requests

API_URL = st.secrets.get("API_URL", "http://translator:8000")

st.title("LEXI-AI — Tradução de Livros (Protótipo)")

uploaded = st.file_uploader("Faça upload do arquivo (TXT ou PDF)", type=["txt","pdf","epub"])
if uploaded is not None:
    st.info(f"Arquivo recebido: {uploaded.name}")
    if st.button("Enviar para tradução"):
        files = {"file": (uploaded.name, uploaded.getvalue())}
        with st.spinner("Enviando..."):
            resp = requests.post(f"{API_URL}/translate/upload", files=files)
        if resp.status_code == 200:
            job = resp.json()
            st.success(f"Job criado: {job['job_id']}")
        else:
            st.error(f"Erro: {resp.text}")

st.subheader("Teste rápido (texto curto)")
text = st.text_area("Cole um trecho em inglês")
if st.button("Traduzir texto curto"):
    if text.strip():
        with st.spinner("Traduzindo..."):
            payload = {"text": text}
            r = requests.post(f"{API_URL}/translate/sync", json=payload)
        if r.status_code == 200:
            st.markdown("**Tradução:**")
            st.write(r.json()["translated"])
        else:
            st.error("Erro ao traduzir")
```

---

### `infra/docker-compose.yml`

```yaml
version: "3.8"
services:
  translator:
    build: ../translator
    volumes:
      - translator_data:/data
    ports:
      - "8000:8000"
  frontend:
    build: ../frontend
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://translator:8000
    depends_on:
      - translator

volumes:
  translator_data:
```

---

### `infra/k8s-deployment.yaml` e `infra/k8s-hpa.yaml`

Incluído no repo: manifests simplificados para Deployment/Service e HPA (mínimas configurações). Ajuste `image` para o seu registry.

---

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install deps
        run: |
          pip install -r translator/requirements.txt
      - name: Basic import test
        run: |
          python -c "import transformers; print('ok')"
```

---

## Instruções de uso e comandos úteis

- Rodar local com Docker Compose:

```bash
cd infra
docker-compose up --build
```

- Rodar worker local (após composer):

```bash
docker-compose exec translator python -m app.worker
```

- Testar endpoint direto (texto curto):

```bash
curl -X POST "http://localhost:8000/translate/sync" -H "Content-Type: application/json" -d '{"text": "Hello world"}'
```

---

## Observações técnicas e próximos passos (prioritizados)

1. **Chunking & loaders:** para PDFs/EPUBs, implemente `pypdf` / `ebooklib` loaders e faça split em chunks (1500 tokens com overlap 200).  
2. **Fila & Workers (produção):** substitua worker polling por Celery/RQ + Redis.  
3. **Storage e rastreabilidade:** use MinIO (S3 compatível) para armazenar inputs/outputs e manter histórico com hashes e metadados do modelo (versão, params).  
4. **Segurança:** add TLS, autenticação (JWT/API keys), validação de uploads e políticas de retenção.  
5. **Melhora de qualidade literária:** experimente prompts de pós‑edição com modelos maiores (Mistral via Ollama) ou use pipelines de pós‑edição humano + LLM.

---

## Licença e notas legais

- Garanta que os arquivos enviados para tradução estejam livres de restrições de copyright ou que você possua autorização. Este projeto é educacional/portfólio: não publique traduções de obras protegidas sem autorização.

---

## Próximo passo

Se estiver ok, eu posso:

- Gerar *os arquivos prontos* (arquivo por arquivo) como um patch que você copia/cola no seu repositório; ou
- Gerar um `tar.gz` com todos os arquivos (se preferir que eu entregue um arquivo baixável).

Qual formato prefere?  

---

*FIM do documento.*
