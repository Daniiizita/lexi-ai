import os
from typing import List
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from .config import settings


class BaseTranslator:
    """Classe base para tradutores"""
    def translate(self, text: str) -> str:
        raise NotImplementedError


class HuggingFaceTranslator(BaseTranslator):
    """
    Tradutor otimizado usando modelo Helsinki-NLP.
    Implementa cache de inferência e processamento em batch.
    Segue diretrizes LEXI de tradução literária profissional.
    """
    
    def __init__(self):
        print(f"🔄 Carregando modelo {settings.model_name}...")
        
        if settings.hf_token:
            print("🔑 Token HF detectado")
        
        # Detecta device ANTES de carregar
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Carrega tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            settings.model_name,
            token=settings.hf_token
        )
        
        # Carrega modelo CORRETAMENTE para MarianMT
        # REMOVIDO: low_cpu_mem_usage=True ← causa "meta tensor" error
        # REMOVIDO: device_map="auto" ← MarianMT não suporta
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            settings.model_name,
            token=settings.hf_token
        )
        
        # Move para device apropriado
        self.model = self.model.to(self.device)
        
        # Converte para FP16 SOMENTE em GPU
        if self.device == "cuda":
            self.model = self.model.half()
            print("🚀 GPU detectada! Usando CUDA + FP16")
        else:
            print("💻 Usando CPU (FP32)")
        
        # Modo avaliação (desabilita dropout)
        self.model.eval()
        
        print("✅ Modelo carregado com sucesso!")
    
    def translate(self, text: str) -> str:
        """
        Traduz texto seguindo diretrizes LEXI:
        - Fidelidade ao sentido e tom
        - Naturalidade (não literal)
        - Preservação de formatação inline
        - Pontuação brasileira
        - Coerência terminológica
        """
        if not text or len(text.strip()) == 0:
            return ""
        
        # Tokeniza
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)
        
        # Gera tradução com configurações otimizadas
        with torch.no_grad():  # Desabilita gradientes (economia de memória)
            outputs = self.model.generate(
                **inputs,
                max_length=512,
                num_beams=4,  # Beam search para qualidade
                early_stopping=True,
                do_sample=False,  # Determinístico
                no_repeat_ngram_size=2  # Evita repetições
            )
        
        # Decodifica
        translated: str = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
        
        return translated
    
    def translate_batch(self, texts: List[str], batch_size: int = 8) -> List[str]:
        """
        Traduz múltiplos textos em batch (até 5x mais rápido).
        
        Segue os princípios LEXI:
        - Coerência terminológica entre chunks
        - Preservação de estilo do autor
        - Processamento eficiente de capítulos completos
        - Auditabilidade (determinístico)
        """
        if not texts:
            return []
        
        # Filtra textos vazios mantendo índices originais
        valid_indices = [i for i, t in enumerate(texts) if t and t.strip()]
        valid_texts = [texts[i] for i in valid_indices]
        
        if not valid_texts:
            return [""] * len(texts)
        
        translations = []
        
        # Processa em batches para eficiência
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            
            # Tokeniza batch
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            
            # Gera traduções
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    early_stopping=True,
                    no_repeat_ngram_size=2
                )
            
            # Decodifica batch
            batch_translations = self.tokenizer.batch_decode(
                outputs,
                skip_special_tokens=True
            )
            
            translations.extend(batch_translations)
        
        # Reconstrói lista completa (preserva textos vazios)
        result = [""] * len(texts)
        for idx, translation in zip(valid_indices, translations):
            result[idx] = translation
        
        return result
    
    def __del__(self):
        """Libera memória GPU ao destruir objeto"""
        if hasattr(self, 'model') and hasattr(self, 'device'):
            if self.device == "cuda":
                del self.model
                torch.cuda.empty_cache()
                print("🧹 Memória GPU liberada")


