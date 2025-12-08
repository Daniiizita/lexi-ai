"""
Módulo de benchmarks de performance do LEXI Translator.

Contém ferramentas para medir e comparar:
- Performance individual vs batch
- Diferentes modelos de tradução
- Impacto de batch_size
- Uso de GPU vs CPU
"""

from .test_perfomance import run_benchmark
from .compare_models import run_comparison

__all__ = ["run_benchmark", "run_comparison"]