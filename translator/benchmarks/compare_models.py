"""
Compara performance entre diferentes configurações do tradutor.

Modelos testados:
- Helsinki-NLP/opus-mt-en-pt (pequeno, rápido)
- Helsinki-NLP/opus-mt-tc-big-en-pt (grande, preciso)

Uso:
    python -m benchmarks.compare_models
"""

import time
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.translate import HuggingFaceTranslator
from app.config import settings
import torch


def benchmark_config(model_name: str, batch_size: int, num_samples: int = 30):
    """
    Benchmark de uma configuração específica.
    
    Args:
        model_name: Nome do modelo no Hugging Face
        batch_size: Tamanho do batch para tradução
        num_samples: Número de textos para traduzir
    
    Returns:
        Tupla (tempo_elapsed, num_traducoes)
    """
    # Sobrescreve config temporariamente
    original_model = settings.model_name
    settings.model_name = model_name
    
    print(f"\n🔄 Testando: {model_name} (batch={batch_size})")
    
    try:
        translator = HuggingFaceTranslator()
        
        texts = [
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning is transforming the world.",
            "Books are portals to different worlds."
        ] * (num_samples // 3)
        
        # Warmup (primeira execução sempre é mais lenta)
        _ = translator.translate_batch(texts[:5], batch_size=batch_size)
        
        # Benchmark real
        start = time.time()
        results = translator.translate_batch(texts, batch_size=batch_size)
        elapsed = time.time() - start
        
        print(f"   ⏱️  Tempo: {elapsed:.2f}s")
        print(f"   📈 Taxa: {len(results)/elapsed:.1f} trad/s")
        
        # Libera memória
        del translator
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Restaura config
        settings.model_name = original_model
        
        return elapsed, len(results)
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        settings.model_name = original_model
        return None, None


def run_comparison():
    """Executa comparação completa entre modelos"""
    
    print("="*60)
    print("LEXI Model Comparison Benchmark")
    print("="*60)
    
    # Detecta hardware
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🖥️  Hardware: {device.upper()}")
    
    if device == "cuda":
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    print("\n" + "="*60)
    print("Iniciando testes...")
    print("="*60)
    
    # Configurações a testar
    configs = [
        ("LukeYang/mix_from_scratch_transformer_big_adafactor_pt2_ja-en_helsinki", 8, "Modelo pequeno"),
        ("LukeYang/mix_from_scratch_transformer_big_adafactor_pt2_ja-en_helsinki", 16, "Modelo pequeno"),
        ("Helsinki-NLP/opus-mt-tc-big-en-pt", 8, "Modelo grande"),
        ("Helsinki-NLP/opus-mt-tc-big-en-pt", 16, "Modelo grande"),
    ]
    
    if device == "cuda":
        configs.append(("Helsinki-NLP/opus-mt-tc-big-en-pt", 32, "Modelo grande"))
    
    results = []
    
    for model, batch, desc in configs:
        elapsed, count = benchmark_config(model, batch, num_samples=30)
        if elapsed:
            results.append({
                "model": model,
                "batch_size": batch,
                "description": desc,
                "time": elapsed,
                "throughput": count / elapsed # type: ignore
            })
    
    # Tabela de resultados
    print("\n" + "="*60)
    print("📊 COMPARAÇÃO FINAL")
    print("="*60)
    print(f"{'Modelo':<20} {'Batch':<8} {'Tempo':<10} {'Throughput'}")
    print("-"*60)
    
    for r in results:
        model_short = r['model'].split('/')[-1][:18]
        print(f"{model_short:<20} {r['batch_size']:<8} {r['time']:.2f}s      {r['throughput']:.1f} trad/s")
    
    print("="*60)
    
    # Recomendação
    if results:
        best = max(results, key=lambda x: x['throughput'])
        print("\n 🏆 Melhor configuração:")
        print(f"   Modelo: {best['model']}")
        print(f"   Batch: {best['batch_size']}")
        print(f"   Throughput: {best['throughput']:.1f} trad/s")


if __name__ == "__main__":
    try:
        run_comparison()
    except KeyboardInterrupt:
        print("\n⚠️ Comparação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante comparação: {e}")
        import traceback
        traceback.print_exc()