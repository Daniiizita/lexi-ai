#!/bin/bash

set -e  # Para execução em caso de erro

echo "🚀 Configurando LEXI-AI Development Environment..."
echo ""

# Verifica se .env existe
if [ ! -f "infra/.env" ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo "📋 Criando .env a partir do template..."
    
    cp infra/.env.example infra/.env
    
    echo ""
    echo "✅ Arquivo .env criado!"
    echo ""
    echo "🔐 ATENÇÃO: Configure as credenciais em infra/.env antes de continuar!"
    echo ""
    echo "Edite o arquivo com:"
    echo "  nano infra/.env"
    echo "  ou"
    echo "  code infra/.env"
    echo ""
    echo "Depois rode novamente: ./scripts/setup_dev.sh"
    exit 1
fi

# Carrega variáveis
export $(cat infra/.env | grep -v '^#' | xargs)

# Verifica se credenciais foram alteradas
if grep -q "change_me_please" infra/.env; then
    echo "❌ ERRO: Você ainda não configurou as senhas em infra/.env"
    echo "📝 Substitua todos os 'change_me_please' por senhas fortes!"
    exit 1
fi

echo "✅ Variáveis de ambiente carregadas!"
echo ""

# Cria pastas necessárias
echo "📁 Criando estrutura de pastas..."
mkdir -p infra/postgres infra/prometheus infra/grafana/dashboards

# Inicia stack
echo "🐳 Iniciando containers..."
cd infra
docker-compose up -d postgres redis minio

# Aguarda serviços
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 15

# Testa conexões
echo ""
echo "🔍 Testando conexões..."

# Postgres
if docker exec lexi-postgres pg_isready -U $POSTGRES_USER > /dev/null 2>&1; then
    echo "✅ PostgreSQL: OK"
else
    echo "❌ PostgreSQL: FALHOU"
fi

# Redis
if docker exec lexi-redis redis-cli -a $REDIS_PASSWORD ping > /dev/null 2>&1; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: FALHOU"
fi

# MinIO
if curl -f http://localhost:$MINIO_PORT/minio/health/live > /dev/null 2>&1; then
    echo "✅ MinIO: OK"
else
    echo "❌ MinIO: FALHOU"
fi

echo ""
echo "🎉 Setup concluído!"
echo ""
echo "📊 Acessos:"
echo "  PostgreSQL:    localhost:$POSTGRES_PORT (user: $POSTGRES_USER)"
echo "  Redis:         localhost:$REDIS_PORT"
echo "  MinIO Console: http://localhost:$MINIO_CONSOLE_PORT"
echo ""
echo "Para iniciar toda a stack:"
echo "  cd infra && docker-compose up -d"