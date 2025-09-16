# All imports consolidated at the top
from fastapi import FastAPI
from pydantic import BaseModel

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# --- RAGService Definition ---
class RAGService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.embedding_model = FakeEmbeddings(size=768)
        self.vector_store = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        dummy_texts = [
            "Style guide: Always translate 'machine learning' as 'aprendizado de máquina'.",
            "Glossary: 'framework' should be translated as 'estrutura de software'.",
            "Glossary: 'backend' should be translated as 'infraestrutura de retaguarda'.",
        ]
        documents = self.text_splitter.create_documents(dummy_texts)
        self.vector_store = Chroma.from_documents(documents=documents, embedding=self.embedding_model)

    def get_retriever(self):
        return self.vector_store.as_retriever()

rag_service = RAGService()

# --- TranslationService Definition ---
class TranslationService:
    def __init__(self):
        self.llm = FakeListLLM(responses=["This is a RAG-powered translated text."])
        retriever = rag_service.get_retriever()
        prompt_template = ChatPromptTemplate.from_template(
            """
            You are a professional book translator. Translate the user's request from {source_lang} to {target_lang}.
            Use the following context to ensure accuracy and consistency with style guides and glossaries.
            If the context is not relevant, ignore it.

            Context:
            {context}

            User's request:
            {input}
            """
        )
        document_chain = create_stuff_documents_chain(self.llm, prompt_template)
        self.retrieval_chain = create_retrieval_chain(retriever, document_chain)

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        response = self.retrieval_chain.invoke({
            "input": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
        })
        return response.get("answer", "Translation failed.")

translation_service = TranslationService()


# --- FastAPI App Definition ---
app = FastAPI(
    title="LEXI-AI",
    description="An AI-powered book translator from English to Portuguese.",
    version="0.1.0",
)

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "English"
    target_lang: str = "Portuguese"

@app.get("/")
def read_root():
    return {"message": "LEXI-AI is running"}

@app.post("/translate")
def translate_text(request: TranslationRequest):
    translated_text = translation_service.translate(
        text=request.text, source_lang=request.source_lang, target_lang=request.target_lang
    )
    return {"translated_text": translated_text}
