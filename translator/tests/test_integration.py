"""
Testes de integração da API.

Requer API rodando (pode usar docker-compose).
"""

import pytest
import requests
import time

API_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def api_health():
    """Verifica se API está rodando"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        assert response.status_code == 200
        return True
    except Exception as e:
        pytest.skip(f"API não está rodando: {e}")


def test_health_endpoint(api_health):
    """Testa endpoint de health"""
    response = requests.get(f"{API_URL}/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_name" in data


def test_translate_sync_endpoint(api_health):
    """Testa tradução síncrona"""
    payload = {"text": "Hello world"}
    
    response = requests.post(
        f"{API_URL}/translate/sync",
        json=payload,
        timeout=30
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "job_id" in data
    assert "translated" in data
    assert len(data["translated"]) > 0


def test_translate_batch_endpoint(api_health):
    """Testa tradução em batch"""
    chunks = [
        {"chunk_id": "1", "plain_text": "Hello"},
        {"chunk_id": "2", "plain_text": "World"},
        {"chunk_id": "3", "plain_text": "Test"}
    ]
    
    response = requests.post(
        f"{API_URL}/translate/batch",
        json=chunks,
        timeout=30
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 3
    assert all("translated_html" in item for item in data)


def test_metrics_endpoint(api_health):
    """Testa endpoint de métricas Prometheus"""
    response = requests.get(f"{API_URL}/metrics")
    
    assert response.status_code == 200
    assert "lexi_http_requests_total" in response.text
    assert "lexi_gpu_memory_used_bytes" in response.text


def test_concurrent_requests(api_health):
    """Testa múltiplas requisições simultâneas"""
    import concurrent.futures
    
    def make_request():
        payload = {"text": "Test sentence"}
        response = requests.post(
            f"{API_URL}/translate/sync",
            json=payload,
            timeout=30
        )
        return response.status_code == 200
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in futures]
    
    assert all(results), "Algumas requisições falharam"


@pytest.mark.slow
def test_large_text_translation(api_health):
    """Testa tradução de texto grande"""
    large_text = " ".join(["Test sentence."] * 100)  # ~200 palavras
    
    payload = {"text": large_text}
    
    start = time.time()
    response = requests.post(
        f"{API_URL}/translate/sync",
        json=payload,
        timeout=60
    )
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 30  # Deve traduzir em menos de 30s