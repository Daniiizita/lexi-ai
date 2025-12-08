# Arquitetura do Sistema de Tradução de PDFs LEXI AI

## Visão Geral

```plaintext
      UPLOAD DO LIVRO (Streamlit)
            ↓
      FRONT chama API FastAPI
            ↓
      API divide em CHUNKS (pedaços)
            ↓
      Envia cada chunk para Redis (fila)
            ↓
      Workers RQ/Celery pegam pedaços
            ↓
      Cada worker roda o modelo:
            Tokenização → Embeddings
            → Multi-Head Attention
            → Feed Forward
            → Normalização
            → Gera tradução
            ↓
      Resultado volta para o worker
            ↓
      Worker junta tudo
            ↓
      Salva no MinIO
            ↓
      API envia link final para o Streamlit
            ↓
      Usuário baixa o livro traduzido

```

### visualmente

``` plaintext
[Streamlit] → [FastAPI] → [Redis] → [Workers + GPU]
                                     ↓
                                  [MinIO]
                                     ↓
                                  Download

```

Tudo isso rodando dentro de containers
gerenciados pelo Kubernetes.
