#!/bin/bash
# filepath: scripts/setup_dev.sh

echo "🚀 Configurando ambiente de desenvolvimento LEXI-AI..."

# Cria pastas necessárias
mkdir -p infra/postgres infra/prometheus infra/grafana/dashboards

# Inicia stack com docker-compose
cd infra
docker-compose up -d postgres redis minio

# Aguarda serviços ficarem prontos
echo "⏳ Aguardando serviços..."
sleep 10

# Roda migrations (se tiver alembic)
# cd ../translator
# alembic upgrade head

echo "✅ Ambiente pronto!"
echo "📊 Acessos:"
echo "  - Postgres: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - MinIO Console: http://localhost:9001"