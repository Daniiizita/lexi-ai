"""
Testes unitários do sistema de tradução.

Uso:
    pytest tests/
"""

import pytest
from app.router import get_translator, reset_translator


@pytest.fixture
def translator():
    """Fixture para reutilizar tradutor entre testes"""
    yield get_translator()
    reset_translator()


def test_translate_single(translator):
    """Testa tradução individual"""
    result = translator.translate("Hello world")
    assert result
    assert isinstance(result, str)
    assert len(result) > 0


def test_translate_empty(translator):
    """Testa tradução de string vazia"""
    result = translator.translate("")
    assert result == ""


def test_translate_batch(translator):
    """Testa tradução em batch"""
    texts = ["Hello", "World", "Test"]
    results = translator.translate_batch(texts)
    
    assert len(results) == len(texts)
    assert all(isinstance(r, str) for r in results)
    assert all(len(r) > 0 for r in results)


def test_batch_with_empty_strings(translator):
    """Testa batch com strings vazias"""
    texts = ["Hello", "", "World"]
    results = translator.translate_batch(texts)
    
    assert len(results) == 3
    assert results[1] == ""
    assert len(results[0]) > 0
    assert len(results[2]) > 0


@pytest.mark.parametrize("batch_size", [4, 8, 16])
def test_different_batch_sizes(translator, batch_size):
    """Testa diferentes tamanhos de batch"""
    texts = ["Test sentence"] * 20
    results = translator.translate_batch(texts, batch_size=batch_size)
    
    assert len(results) == len(texts)