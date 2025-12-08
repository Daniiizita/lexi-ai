"""
Benchmark de performance do tradutor LEXI.
Compara tradução individual vs. batch processing.

Uso:
    python -m benchmarks.test_perfomance
"""

import time
import sys
from pathlib import Path

# Adiciona raiz do projeto ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.router import get_translator


def run_benchmark():
    """Executa benchmark completo de performance"""
    
    print("="*60)
    print("LEXI Translation Performance Benchmark")
    print("="*60 + "\n")
    
    # Carrega tradutor (singleton)
    print("🔄 Carregando modelo...")
    translator = get_translator()
    print("✅ Modelo carregado!\n")
    
    # Dataset de teste (textos literários variados)
    texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is transforming the world.",
        "Books are portals to different worlds.",
        "Artificial intelligence enables new possibilities.",
        "Translation requires understanding context and culture.",
        "The sun was setting over the distant mountains.",
        "She walked through the crowded streets of the city.",
        "Time passes differently when you're having fun.",
        "Knowledge is power, but wisdom is understanding.",
        "The journey of a thousand miles begins with a single step."
    ] * 3  # 30 textos
    
    print(f"📊 Dataset: {len(texts)} textos\n")
    
    # Teste 1: Tradução individual
    print("🔵 Teste 1: Tradução Individual")
    start = time.time()
    individual_results = []
    for text in texts:
        result = translator.translate(text)
        individual_results.append(result)
    individual_time = time.time() - start
    print(f"   ⏱️  Tempo: {individual_time:.2f}s")
    print(f"   📈 Taxa: {len(texts)/individual_time:.1f} traduções/s\n")
    
    # Teste 2: Batch processing (8)
    print("🟢 Teste 2: Batch Processing (batch_size=8)")
    start = time.time()
    batch_results_8 = translator.translate_batch(texts, batch_size=8)
    batch_time_8 = time.time() - start
    print(f"   ⏱️  Tempo: {batch_time_8:.2f}s")
    print(f"   📈 Taxa: {len(texts)/batch_time_8:.1f} traduções/s\n")
    
    # Teste 3: Batch processing (16)
    print("🟣 Teste 3: Batch Processing (batch_size=16)")
    start = time.time()
    batch_results_16 = translator.translate_batch(texts, batch_size=16)
    batch_time_16 = time.time() - start
    print(f"   ⏱️  Tempo: {batch_time_16:.2f}s")
    print(f"   📈 Taxa: {len(texts)/batch_time_16:.1f} traduções/s\n")
    
    # Teste 4: Batch processing (32) - apenas se GPU disponível
    import torch
    if torch.cuda.is_available():
        print("🟡 Teste 4: Batch Processing (batch_size=32)")
        start = time.time()
        batch_results_32 = translator.translate_batch(texts, batch_size=32)
        batch_time_32 = time.time() - start
        print(f"   ⏱️  Tempo: {batch_time_32:.2f}s")
        print(f"   📈 Taxa: {len(texts)/batch_time_32:.1f} traduções/s\n")
    
    # Resultados finais
    print("="*60)
    print("📊 RESULTADOS FINAIS")
    print("="*60)
    print(f"Individual:      {individual_time:.2f}s  (baseline)")
    print(f"Batch (8):       {batch_time_8:.2f}s  (🚀 {individual_time/batch_time_8:.1f}x mais rápido)")
    print(f"Batch (16):      {batch_time_16:.2f}s  (🚀 {individual_time/batch_time_16:.1f}x mais rápido)")
    
    if torch.cuda.is_available():
        print(f"Batch (32):      {batch_time_32:.2f}s  (🚀 {individual_time/batch_time_32:.1f}x mais rápido)")
    
    print("="*60 + "\n")
    
    # Valida consistência
    print("🔍 Validando Consistência...")
    if len(individual_results) == len(batch_results_8) == len(batch_results_16):
        print("✅ Todas as traduções retornaram resultados válidos")
    else:
        print("❌ ERRO: Número de resultados inconsistente!")
        return
    
    # Amostra de tradução
    print(f"\n📝 Exemplo de Tradução:")
    print(f"   Original: {texts[0]}")
    print(f"   Traduzido: {batch_results_16[0]}")
    
    # Estatísticas de GPU (se disponível)
    if torch.cuda.is_available():
        print(f"\n🎮 Estatísticas de GPU:")
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   VRAM Total: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        print(f"   VRAM Usada: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
        print(f"   VRAM Peak: {torch.cuda.max_memory_allocated(0) / 1e9:.2f} GB")


if __name__ == "__main__":
    try:
        run_benchmark()
    except KeyboardInterrupt:
        print("\n⚠️ Benchmark cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante benchmark: {e}")
        import traceback
        traceback.print_exc()