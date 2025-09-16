# LEXI-AI
LEXI – The AI that translates books like a true language expert.

LEXI is an innovative artificial intelligence capable of translating books from English to Portuguese with precision and natural flow. Unlike conventional translators, LEXI understands the linguistic essence of each country, interpreting cultural and idiomatic expressions to provide a smooth and engaging reading experience.

## Project Status: Functional Prototype

This repository contains a functional prototype of the LEXI-AI translation service. It includes a basic FastAPI server with a RAG (Retrieval-Augmented Generation) pipeline for context-aware translation.

**Note on Structure:** Due to challenges with the Python import system in the development environment, the project has been structured as a single-file application (`lexi_ai/main.py`). This is a temporary workaround to ensure functionality. The original plan was a more modular, multi-file architecture.

## Getting Started

### Prerequisites
- Python 3.9+
- `pip` for package installation

### Installation
1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd lexi-ai
   ```
2. Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

### Running the Application
To run the FastAPI server, use the following command from the project root:
```sh
uvicorn lexi_ai.main:app --host 0.0.0.0 --port 8000
```
The server will be available at `http://0.0.0.0:8000`.

### Running Tests
To run the test suite, first install the development dependencies:
```sh
pip install -r requirements-dev.txt
```
Then, run `pytest`:
```sh
pytest
```

## API Usage

The main endpoint is `/translate`. You can send a `POST` request with the text you want to translate.

### Example with `curl`
```sh
curl -X POST -H "Content-Type: application/json" \
-d '{"text": "Hello, how are you?"}' \
http://localhost:8000/translate
```

### Example Response
```json
{
  "translated_text": "This is a RAG-powered translated text."
}
```
**Note:** The current implementation uses a mock language model, so the translation returned will always be the same placeholder text.

---
*Tradução do README para Português*

# LEXI-AI
LEXI – A IA que traduz livros como um verdadeiro especialista.

LEXI é uma inteligência artificial inovadora capaz de traduzir livros do inglês para o português com precisão e naturalidade.

## Status do Projeto: Protótipo Funcional

Este repositório contém um protótipo funcional do serviço de tradução LEXI-AI. Inclui um servidor FastAPI básico com um pipeline RAG (Geração Aumentada por Recuperação) para tradução sensível ao contexto.

**Nota sobre a Estrutura:** Devido a desafios com o sistema de importação do Python no ambiente de desenvolvimento, o projeto foi estruturado como uma aplicação de ficheiro único (`lexi_ai/main.py`). Esta é uma solução temporária para garantir a funcionalidade.

## Como Começar

### Instalação
```sh
pip install -r requirements.txt
```

### Executar a Aplicação
```sh
uvicorn lexi_ai.main:app --host 0.0.0.0 --port 8000
```

### Executar os Testes
```sh
pip install -r requirements-dev.txt
pytest
```

### Uso da API com `curl`
```sh
curl -X POST -H "Content-Type: application/json" \
-d '{"text": "Hello, how are you?"}' \
http://localhost:8000/translate
```
