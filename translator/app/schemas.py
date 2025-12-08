from pydantic import BaseModel, Field
from typing import Optional, List


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Texto a ser traduzido")


class TranslationResponse(BaseModel):
    job_id: str
    translated: Optional[str] = None


class ChunkInput(BaseModel):
    """Schema para tradução por chunks (modo profissional)"""
    chunk_id: str
    plain_text: str
    inline_markup: Optional[str] = ""
    context_before: Optional[str] = ""
    context_after: Optional[str] = ""
    glossary: Optional[str] = ""
    style_guide: Optional[str] = ""


class ChunkOutput(BaseModel):
    """Saída estruturada conforme README.md"""
    chunk_id: str
    translated_html: str
    decisions: List[str] = []
    terms_used: List[str] = []
    flags: List[str] = []