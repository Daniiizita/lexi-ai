import os
from typing import Optional
from .translate import HuggingFaceTranslator


# Singleton global (carrega uma vez no startup)
_translator_instance: Optional[HuggingFaceTranslator] = None


def get_translator() -> HuggingFaceTranslator:
    """
    Factory pattern com singleton para reutilizar modelo carregado.
    Carrega o modelo apenas uma vez no primeiro uso.
    """
    global _translator_instance
    
    if _translator_instance is None:
        provider = os.getenv("MODEL_PROVIDER", "HF")
        
        if provider == "HF":
            _translator_instance = HuggingFaceTranslator()
        else:
            raise ValueError(f"Provedor '{provider}' não suportado. Use MODEL_PROVIDER=HF")
    
    return _translator_instance


def reset_translator():
    """Força recarga do modelo (útil para testes)"""
    global _translator_instance
    _translator_instance = None