# LEXI-AI

An English → Brazilian Portuguese translation service for books and long texts, built with FastAPI, Hugging Face Transformers and Streamlit. It is an early-stage prototype, with a roadmap towards literary-quality translation.

> **Status:** prototype (v0.2.0). Today the service translates text with the open-source `Helsinki-NLP/opus-mt-en-pt` neural machine-translation model. The literary-translation goals described below (style preservation, glossary-aware terminology, idiom adaptation) are the project's direction and are **not implemented yet**. See [What works today](#what-works-today).

<!-- TODO: confirmar — o README original descrevia o LEXI como uma IA que "compreende a essência linguística", preserva estilo, metáforas e gírias. O código atual usa apenas o modelo MarianMT (opus-mt-en-pt), sem glossário nem guia de estilo. Confirmar como posicionar o projeto para recrutadores. -->

## Tech stack

| Area | Technology |
| --- | --- |
| API | Python 3.11, FastAPI, Uvicorn, Pydantic |
| Translation model | `Helsinki-NLP/opus-mt-en-pt` (MarianMT) via Hugging Face `transformers` + PyTorch |
| Web UI | Streamlit |
| Containers | Docker, Docker Compose |
| Orchestration (manifests) | Kubernetes Deployment, Service and HorizontalPodAutoscaler |
| Tests / CI | pytest; GitHub Actions |

## What works today

- **`POST /translate/sync`**: translate a short text (up to 512 tokens) and get the result back immediately.
- **`POST /translate`** and **`POST /translate/batch`**: translate structured chunks (`chunk_id`, text, and the text before/after as context). The batch endpoint tokenizes and generates in groups of 8 for throughput.
- **`POST /translate/upload`** plus a **background worker**: upload a file, get a `job_id`, and let a worker translate it in the background. The result is written to the `storage/` folder next to the uploaded file as `<job_id>_<filename>.<lang>.translated.txt`.
- **`GET /health`**: health check reporting the environment and the configured model.
- **Streamlit front end** with an API status indicator, file upload and a quick-translation box.
- **GPU support**: the model runs on CUDA in FP16 when a GPU is available and falls back to CPU (FP32) otherwise.
- **Model-provider factory** (`MODEL_PROVIDER`, currently only `HF`) with a singleton, so the model is loaded once at startup rather than per request.

### Known limitations

- The worker reads uploaded files as UTF-8 plain text. PDF and EPUB are accepted by the UI but are not parsed yet (`TODO` in `translator/app/worker.py`).
- The chunk schema accepts `glossary`, `style_guide` and `inline_markup`, but the translator does not use them yet; the `decisions`, `terms_used` and `flags` fields in responses are always empty.
- There is no result-download endpoint yet: finished translations are files in the `storage/` folder.
- `infra/docker-compose.yml` starts the API and the Streamlit front end, but not the background worker.

## Getting started

### Prerequisites

- Python 3.11
- Enough disk space and memory to download and run the translation model (it is fetched from the Hugging Face Hub on first start). A GPU is optional.

### Run the API

```bash
cd translator
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Interactive API docs are at <http://localhost:8000/docs>. Configuration comes from environment variables (`MODEL_NAME`, `MODEL_PROVIDER`, `STORAGE_DIR`, `HF_TOKEN`, `LOG_LEVEL`) and an optional `translator/.env.<ENVIRONMENT>` file (for example `.env.development`); defaults are in `translator/app/config.py`.

Quick check:

```bash
curl -X POST http://localhost:8000/translate/sync \
  -H "Content-Type: application/json" \
  -d '{"text": "The quick brown fox jumps over the lazy dog."}'
```

### Run the background worker (for file uploads)

In a second terminal, from the `translator/` folder with the same virtual environment:

```bash
python -m app.worker
```

The worker polls `STORAGE_DIR` every 5 seconds for `*.pending` files created by `/translate/upload`.

### Run the Streamlit front end

```bash
cd frontend
pip install -r requirements.txt
API_URL=http://localhost:8000 streamlit run app.py
```

### Run with Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```

The API is exposed on port 8000 and the front end on <http://localhost:8501>.

### Run the tests

```bash
cd translator
python -m pytest tests/
```

The tests load the real model, so the first run downloads it.

## Architecture

```
[Streamlit UI] → [FastAPI translator API] → storage/ (.pending flag) → [Worker polling loop] → translated .txt
                         │
                         └→ in-process HuggingFaceTranslator (singleton, CUDA FP16 or CPU)
```

The repository contains Kubernetes manifests in [`infra/`](infra/): a `translator` Deployment with CPU/memory requests and limits, a ClusterIP Service, and a HorizontalPodAutoscaler (1 to 4 replicas, targeting 60% CPU).

[`ARCHITECTURE.md`](ARCHITECTURE.md) describes the **target design**, in which the API splits books into chunks, queues them in Redis, workers on GPUs translate them and results are stored in MinIO. Redis, MinIO and chunking are not part of the code yet; the current queue is the file-based `.pending` mechanism described above.

## Technical highlight: a deliberately simple job queue

To keep the prototype dependency-free, asynchronous jobs use the filesystem as the queue: the API stores the upload and drops a `<file>.pending` marker containing the target language; the worker finds markers, translates the file, writes the output and deletes the marker. It is easy to run and inspect, and its interface (upload → job id → output file) is the same one a Redis-based queue would expose, which is the migration planned in `ARCHITECTURE.md`.

## Roadmap

From the project's own design notes ([`ARCHITECTURE.md`](ARCHITECTURE.md), [`.github/instructions/behavior_prompt.instructions.md`](.github/instructions/behavior_prompt.instructions.md)): chunking of full books, a Redis queue with scalable workers, result storage with download links, PDF/EPUB parsing, glossary and style-guide support, and human-review flags for ambiguous passages.

<!-- TODO: confirmar — `requirements.txt` na raiz lista `google-genai` e `dotenv`, mas nenhum código usa esses pacotes. Confirmar se faz parte de um plano (ex.: provedor Gemini) ou se pode ser removido. -->
<!-- TODO: confirmar — o CI só instala as dependências e importa `transformers`; os testes de `translator/tests` não rodam no CI. -->

## Notes

The previous (Portuguese/English) project description is preserved in [`old_README.md`](old_README.md).
