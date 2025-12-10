"""
Testes do sistema de chunking inteligente.
"""

import pytest
from app.chunking import IntelligentChunker
from app.config import settings


@pytest.fixture
def chunker():
    """Fixture com chunker configurado"""
    return IntelligentChunker(
        model_name=settings.model_name,
        max_tokens=450,
        overlap_tokens=50
    )


def test_chunk_simple_text(chunker):
    """Testa chunking de texto simples"""
    text = "Hello world. " * 100  # 200 palavras
    
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, tuple) for chunk in chunks)
    assert all(len(chunk) == 2 for chunk in chunks)  # (text, metadata)


def test_chunk_respects_token_limit(chunker):
    """Garante que chunks não excedem limite de tokens"""
    text = "Very long sentence. " * 1000
    
    chunks = chunker.chunk_text(text)
    
    for chunk_text, metadata in chunks:
        assert metadata['token_count'] <= chunker.max_tokens


def test_chunk_overlap(chunker):
    """Verifica overlap entre chunks consecutivos"""
    text = ("Paragraph one with some content.\n\n"
            "Paragraph two with more content.\n\n"
            "Paragraph three with even more content.\n\n") * 50
    
    chunks = chunker.chunk_text(text)
    
    if len(chunks) > 1:
        # Pega últimas palavras do chunk 1
        first_chunk_end = chunks[0][0].split()[-10:]
        # Pega primeiras palavras do chunk 2
        second_chunk_start = chunks[1][0].split()[:20]
        
        # Deve ter overlap
        overlap = set(first_chunk_end) & set(second_chunk_start)
        assert len(overlap) > 0, "Chunks devem ter overlap"


def test_chunk_metadata(chunker):
    """Verifica completude dos metadados"""
    text = "Test paragraph.\n\n" * 100
    
    chunks = chunker.chunk_text(text)
    
    for chunk_text, metadata in chunks:
        assert 'index' in metadata
        assert 'token_count' in metadata
        assert 'start_para' in metadata
        assert 'end_para' in metadata
        assert metadata['token_count'] > 0


def test_get_stats(chunker):
    """Testa geração de estatísticas"""
    text = "Sample text. " * 500
    
    chunks = chunker.chunk_text(text)
    stats = chunker.get_stats(chunks)
    
    assert 'total_chunks' in stats
    assert 'avg_tokens' in stats
    assert 'min_tokens' in stats
    assert 'max_tokens' in stats
    assert stats['total_chunks'] == len(chunks)


def test_large_paragraph_splitting(chunker):
    """Testa divisão de parágrafos muito grandes"""
    # Parágrafo com 600 sentenças (vai exceder max_tokens)
    large_para = ". ".join(["Long sentence here"] * 600)
    
    chunks = chunker.chunk_text(large_para)
    
    # Deve dividir em múltiplos chunks
    assert len(chunks) > 1
    
    # Todos devem respeitar limite
    for chunk_text, metadata in chunks:
        assert metadata['token_count'] <= chunker.max_tokens