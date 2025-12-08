# Arquitetura 

## 🎯 Arquitetura Completa de Produção

### Stack Completa (Padrão Mercado)

``` plaintext

Frontend (Streamlit)
    ↓
API Gateway (FastAPI + Kong/Traefik)
    ↓
Redis (Queue + Cache)
    ↓
Celery Workers (GPU-accelerated)
    ↓
PostgreSQL (Metadata + Jobs)
    ↓
MinIO/S3 (Storage)
    ↓
Prometheus + Grafana (Metrics)
    ↓
ELK Stack (Logs)
    ↓
Kubernetes (Orchestration)
```

---

## 📊 Nova Estrutura do Projeto

``` plaintext
lexi-ai/
├── frontend/                    # Streamlit UI
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── translator/                  # FastAPI Core
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # API principal
│   │   ├── config.py           # Config centralizado
│   │   ├── schemas.py          # Pydantic models
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── translate.py        # Tradutor HF
│   │   ├── tasks.py            # Celery tasks
│   │   ├── database.py         # DB connection
│   │   └── logger.py           # Logging estruturado
│   ├── celery_worker.py        # Celery entrypoint
│   ├── Dockerfile
│   └── requirements.txt
├── infra/
│   ├── docker-compose.yml      # Stack completa local
│   ├── redis/
│   │   └── redis.conf
│   ├── postgres/
│   │   └── init.sql
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/
│   ├── elasticsearch/
│   │   └── elasticsearch.yml
│   ├── minio/
│   │   └── config.json
│   └── k8s/
│       ├── namespace.yaml
│       ├── redis-deployment.yaml
│       ├── postgres-deployment.yaml
│       ├── minio-deployment.yaml
│       ├── api-deployment.yaml
│       ├── worker-deployment.yaml
│       ├── frontend-deployment.yaml
│       ├── ingress.yaml
│       └── monitoring/
├── scripts/
│   ├── setup_dev.sh
│   ├── deploy_k8s.sh
│   └── backup_db.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/
    ├── API.md
    ├── DEPLOYMENT.md
    └── MONITORING.md
```