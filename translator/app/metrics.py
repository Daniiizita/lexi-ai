"""
Métricas Prometheus para observabilidade.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
import functools
from typing import Callable
from .logger import logger


# ==================== MÉTRICAS ====================

# Requisições HTTP
http_requests_total = Counter(
    'lexi_http_requests_total',
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'lexi_http_request_duration_seconds',
    'Duração das requisições HTTP',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Traduções
translation_requests_total = Counter(
    'lexi_translation_requests_total',
    'Total de requisições de tradução',
    ['endpoint', 'status']
)

translation_duration_seconds = Histogram(
    'lexi_translation_duration_seconds',
    'Tempo de tradução',
    ['endpoint', 'batch_size'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

translation_tokens_processed = Counter(
    'lexi_translation_tokens_processed_total',
    'Total de tokens traduzidos',
    ['model']
)

translation_chunks_processed = Counter(
    'lexi_translation_chunks_processed_total',
    'Total de chunks traduzidos',
    ['status']
)

# Jobs
active_translation_jobs = Gauge(
    'lexi_active_translation_jobs',
    'Jobs de tradução ativos'
)

translation_job_duration_seconds = Histogram(
    'lexi_translation_job_duration_seconds',
    'Duração completa de jobs',
    buckets=(10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0)
)

translation_job_chunks_total = Histogram(
    'lexi_translation_job_chunks_total',
    'Chunks por job',
    buckets=(1, 5, 10, 25, 50, 100, 200, 500, 1000)
)

# GPU
gpu_memory_used_bytes = Gauge(
    'lexi_gpu_memory_used_bytes',
    'Memória GPU usada em bytes',
    ['device']
)

gpu_utilization_percent = Gauge(
    'lexi_gpu_utilization_percent',
    'Utilização da GPU em %',
    ['device']
)

# Modelo
model_info = Info(
    'lexi_model',
    'Informações do modelo de tradução'
)


# ==================== DECORATORS ====================

def track_translation(endpoint: str, batch_size: int = 1):
    """Decorator para rastrear métricas de tradução"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            translation_requests_total.labels(endpoint=endpoint, status='started').inc()
            
            start = time.time()
            try:
                result = func(*args, **kwargs)
                
                duration = time.time() - start
                translation_duration_seconds.labels(
                    endpoint=endpoint,
                    batch_size=str(batch_size)
                ).observe(duration)
                
                translation_requests_total.labels(endpoint=endpoint, status='success').inc()
                
                return result
                
            except Exception as e:
                translation_requests_total.labels(endpoint=endpoint, status='error').inc()
                raise
        
        return wrapper
    return decorator


def update_gpu_metrics():
    """Atualiza métricas de GPU (se disponível)"""
    try:
        import torch
        
        if torch.cuda.is_available():
            for device_id in range(torch.cuda.device_count()):
                # Memória
                memory_allocated = torch.cuda.memory_allocated(device_id)
                gpu_memory_used_bytes.labels(device=f"cuda:{device_id}").set(memory_allocated)
                
                # Utilização (aproximação via memory)
                total_memory = torch.cuda.get_device_properties(device_id).total_memory
                utilization = (memory_allocated / total_memory) * 100
                gpu_utilization_percent.labels(device=f"cuda:{device_id}").set(utilization)
                
    except Exception as e:
        logger.warning(f"Erro ao atualizar métricas GPU: {e}")


def set_model_info(model_name: str, model_provider: str, environment: str):
    """Define informações do modelo"""
    model_info.info({
        'model_name': model_name,
        'model_provider': model_provider,
        'environment': environment
    })