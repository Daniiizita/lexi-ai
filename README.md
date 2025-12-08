# LEXI-AI

## LEXI – The AI that translates books like a true language expert

LEXI is an innovative artificial intelligence capable of translating books from English to Portuguese with precision and natural flow. Unlike conventional translators, LEXI understands the linguistic essence of each country, interpreting cultural and idiomatic expressions to provide a smooth and engaging reading experience.

With advanced natural language processing technology, LEXI preserves the author's style, ensuring that metaphors, slang, and nuances of the original text are conveyed authentically. Whether it's a novel, a technical book, or a classic work, LEXI delivers translations that respect context and make the reading experience as rich as in the original language.

Tradução: LEXI é uma inteligência artificial inovadora capaz de traduzir livros do inglês para o português com precisão e naturalidade. Diferente de tradutores convencionais, LEXI compreende a essência linguística de cada país, interpretando expressões culturais e idiomáticas para oferecer uma leitura fluida e envolvente.

Com tecnologia avançada de processamento de linguagem natural, LEXI preserva o estilo do autor, garantindo que metáforas, gírias e nuances do texto original sejam transmitidos com autenticidade. Seja um romance, um livro técnico ou uma obra clássica, LEXI entrega traduções que respeitam o contexto e tornam a experiência de leitura tão rica quanto no idioma original.

## Performance

### Benchmarks (GPU NVIDIA)

| Hardware | Método | Tempo (30 textos) | Throughput |
|----------|--------|-------------------|------------|
| RTX 3060 | Individual | 3.09s | 9.7 trad/s |
| RTX 3060 | Batch (16) | 0.74s | **40.5 trad/s** |

**Speedup vs CPU:** 57x mais rápido 🚀

### Requisitos

- **GPU**: NVIDIA com CUDA 11.8+
- **VRAM**: 4GB+ (8GB recomendado para batch=32)
- **Drivers**: nvidia-smi 535+

### Rodar Benchmark

```bash
cd translator
python -m benchmarks.test_perfomance
```

## 🔒 Segurança e Credenciais

### Setup Inicial

1. **Copie os templates de ambiente:**
   ```bash
   cp translator/.env.example translator/.env.development
   cp infra/.env.example infra/.env
   ```

2. **Configure credenciais seguras:**
   
   **Gere senhas fortes:**
   ```bash
   # PostgreSQL
   openssl rand -base64 32

   # Redis
   openssl rand -base64 32

   # MinIO
   openssl rand -base64 32

   # Grafana
   openssl rand -base64 32
   ```

3. **Obtenha token do Hugging Face:**
   - Acesse: https://huggingface.co/settings/tokens
   - Crie um token com permissão `read`
   - Cole em `HF_TOKEN`

### ⚠️ NUNCA Commite

- Arquivos `.env` com credenciais reais
- Tokens de API
- Senhas em texto plano
- Arquivo `credenciais.md` (já está no `.gitignore`)

### Produção

Em produção, use **Secrets Managers**:

- **Kubernetes:** Secrets + Sealed Secrets
- **Docker Swarm:** Docker Secrets
- **Cloud:** AWS Secrets Manager / Azure Key Vault / GCP Secret Manager