"""
Chunking inteligente com tokenizer real do modelo.

Divide texto preservando contexto semântico e overlap.
"""

from typing import List, Tuple, Dict
from transformers import AutoTokenizer
from .config import settings
from .logger import logger


class IntelligentChunker:
    """
    Divide texto em chunks inteligentes usando o tokenizer do modelo.
    
    Features:
    - Tokenização real (não aproximação por palavras)
    - Overlap configurável para manter contexto
    - Respeita limites de parágrafos/sentenças
    - Metadados para auditoria
    """
    
    def __init__(
        self, 
        model_name: str = None, # type: ignore
        max_tokens: int = 450,  # ← Deixa margem para tokens especiais
        overlap_tokens: int = 50
    ):
        """
        Args:
            model_name: Nome do modelo HF (usa settings se None)
            max_tokens: Tokens máximos por chunk (< 512 do modelo)
            overlap_tokens: Tokens de overlap entre chunks
        """
        self.model_name = model_name or settings.model_name
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        
        logger.info(f"🔧 Inicializando chunker para {self.model_name}")
        
        # Carrega tokenizer (leve, não é o modelo completo)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            token=settings.hf_token
        )
        
        logger.info(f"✅ Chunker pronto | max_tokens={max_tokens} | overlap={overlap_tokens}")
    
    def chunk_text(self, text: str) -> List[Tuple[str, Dict]]:
        """
        Divide texto em chunks com metadados.
        
        Args:
            text: Texto completo a dividir
        
        Returns:
            Lista de tuplas (chunk_text, metadata)
            
        Example:
            >>> chunker = IntelligentChunker()
            >>> chunks = chunker.chunk_text("Long book text...")
            >>> for chunk_text, metadata in chunks:
            ...     print(f"Chunk {metadata['index']}: {len(chunk_text)} chars")
        """
        # 1. Split em parágrafos (preserva estrutura semântica)
        paragraphs = self._split_paragraphs(text)
        
        chunks = []
        current_chunk_paras = []
        current_tokens = 0
        chunk_index = 0
        
        for para_idx, para in enumerate(paragraphs):
            # Tokeniza parágrafo
            para_tokens = self.tokenizer.encode(
                para, 
                add_special_tokens=False,  # Não conta <s> </s> ainda
                truncation=False
            )
            para_token_count = len(para_tokens)
            
            # Verifica se cabe no chunk atual
            if current_tokens + para_token_count <= self.max_tokens:
                # Adiciona ao chunk atual
                current_chunk_paras.append(para)
                current_tokens += para_token_count
            else:
                # Chunk atual está cheio: salva e inicia novo
                if current_chunk_paras:
                    chunk_text = '\n\n'.join(current_chunk_paras)
                    metadata = self._build_metadata(
                        chunk_index, 
                        current_tokens,
                        para_idx - len(current_chunk_paras),
                        para_idx - 1
                    )
                    chunks.append((chunk_text, metadata))
                    chunk_index += 1
                
                # Inicia novo chunk com overlap
                overlap_paras = self._get_overlap_paragraphs(
                    current_chunk_paras,
                    self.overlap_tokens
                )
                
                # Se parágrafo atual é muito grande, divide por sentenças
                if para_token_count > self.max_tokens:
                    sentence_chunks = self._chunk_large_paragraph(para, para_idx)
                    chunks.extend(sentence_chunks)
                    chunk_index += len(sentence_chunks)
                    
                    # Reseta chunk atual
                    current_chunk_paras = []
                    current_tokens = 0
                else:
                    # Inicia novo chunk com overlap + parágrafo atual
                    current_chunk_paras = overlap_paras + [para]
                    current_tokens = sum(
                        len(self.tokenizer.encode(p, add_special_tokens=False))
                        for p in current_chunk_paras
                    )
        
        # Último chunk
        if current_chunk_paras:
            chunk_text = '\n\n'.join(current_chunk_paras)
            metadata = self._build_metadata(
                chunk_index,
                current_tokens,
                len(paragraphs) - len(current_chunk_paras),
                len(paragraphs) - 1
            )
            chunks.append((chunk_text, metadata))
        
        logger.info(f"📊 Texto dividido em {len(chunks)} chunks")
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split em parágrafos preservando vazios"""
        # Split por dupla quebra de linha
        paras = text.split('\n\n')
        # Remove vazios mas preserva estrutura
        return [p.strip() for p in paras if p.strip()]
    
    def _get_overlap_paragraphs(
        self, 
        paragraphs: List[str], 
        target_tokens: int
    ) -> List[str]:
        """
        Pega últimos parágrafos que somam ~target_tokens.
        Garante contexto para o próximo chunk.
        """
        if not paragraphs:
            return []
        
        overlap_paras = []
        token_count = 0
        
        # Pega de trás pra frente
        for para in reversed(paragraphs):
            para_tokens = len(self.tokenizer.encode(para, add_special_tokens=False))
            
            if token_count + para_tokens <= target_tokens:
                overlap_paras.insert(0, para)
                token_count += para_tokens
            else:
                break
        
        return overlap_paras
    
    def _chunk_large_paragraph(
        self, 
        paragraph: str, 
        para_idx: int
    ) -> List[Tuple[str, Dict]]:
        """
        Divide parágrafo muito grande em chunks menores por sentenças.
        """
        # Split por ponto final (aproximação simples)
        sentences = [s.strip() + '.' for s in paragraph.split('. ') if s.strip()]
        
        chunks = []
        current_sentences = []
        current_tokens = 0
        
        for sent in sentences:
            sent_tokens = len(self.tokenizer.encode(sent, add_special_tokens=False))
            
            if current_tokens + sent_tokens <= self.max_tokens:
                current_sentences.append(sent)
                current_tokens += sent_tokens
            else:
                if current_sentences:
                    chunk_text = ' '.join(current_sentences)
                    metadata = {
                        'index': -1,  # Será atualizado pelo caller
                        'token_count': current_tokens,
                        'start_para': para_idx,
                        'end_para': para_idx,
                        'is_split_paragraph': True
                    }
                    chunks.append((chunk_text, metadata))
                
                current_sentences = [sent]
                current_tokens = sent_tokens
        
        # Última sentença
        if current_sentences:
            chunk_text = ' '.join(current_sentences)
            metadata = {
                'index': -1,
                'token_count': current_tokens,
                'start_para': para_idx,
                'end_para': para_idx,
                'is_split_paragraph': True
            }
            chunks.append((chunk_text, metadata))
        
        return chunks
    
    def _build_metadata(
        self,
        index: int,
        token_count: int,
        start_para: int,
        end_para: int
    ) -> Dict:
        """Constrói metadados do chunk"""
        return {
            'index': index,
            'token_count': token_count,
            'start_para': start_para,
            'end_para': end_para,
            'model': self.model_name,
            'max_tokens': self.max_tokens,
            'overlap_tokens': self.overlap_tokens
        }
    
    def get_stats(self, chunks: List[Tuple[str, Dict]]) -> Dict:
        """Estatísticas dos chunks gerados"""
        if not chunks:
            return {}
        
        token_counts = [meta['token_count'] for _, meta in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_tokens': sum(token_counts) / len(token_counts),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'total_tokens': sum(token_counts)
        }