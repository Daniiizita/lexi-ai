import streamlit as st
import requests
import os


# Prioriza variável de ambiente, depois secrets, depois fallback local
API_URL = os.getenv("API_URL") or st.secrets.get("API_URL", "http://localhost:8000")


st.set_page_config(
    page_title="LEXI AI - Tradução Literária",
    page_icon="📚",
    layout="wide"
)

st.title("📚 LEXI AI — Tradução Literária Profissional")
st.caption("Traduza livros do inglês para português-Brasil com naturalidade e precisão")

# Mostra status da API
with st.sidebar:
    st.subheader("🔌 Status da API")
    try:
        health = requests.get(f"{API_URL}/health", timeout=2)
        if health.status_code == 200:
            data = health.json()
            st.success("✅ API Online")
            st.json(data)
        else:
            st.error("❌ API com problemas")
    except Exception as e:
        st.error(f"❌ API offline: {e}")
        st.warning("Certifique-se de que a API está rodando em http://localhost:8000")

st.divider()

# Upload de arquivo
st.subheader("📤 Upload de Livro Completo")
st.caption("Suporta: TXT, PDF, EPUB (processamento assíncrono via worker)")

uploaded = st.file_uploader(
    "Selecione o arquivo",
    type=["txt", "pdf", "epub"],
    help="O arquivo será processado em segundo plano pelo worker"
)

if uploaded is not None:
    st.info(f"📁 Arquivo: **{uploaded.name}** ({uploaded.size} bytes)")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        target_lang = st.selectbox("Idioma de destino", ["pt", "pt-BR"], index=1)
    
    if st.button("🚀 Enviar para tradução", type="primary", use_container_width=True):
        files = {"file": (uploaded.name, uploaded.getvalue())}
        
        with st.spinner("Enviando arquivo..."):
            try:
                resp = requests.post(
                    f"{API_URL}/translate/upload",
                    files=files,
                    params={"target_lang": target_lang},
                    timeout=30
                )
                
                if resp.status_code == 200:
                    job = resp.json()
                    st.success("✅ Job criado com sucesso!")
                    st.code(f"Job ID: {job['job_id']}\nStatus: {job['status']}", language="json")
                    st.info("💡 O worker está processando. Verifique a pasta `storage/` para o resultado.")
                else:
                    st.error(f"❌ Erro {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Erro ao enviar: {e}")

st.divider()

# Teste rápido
st.subheader("⚡ Teste Rápido (Tradução Síncrona)")
st.caption("Para trechos pequenos de texto (≤512 tokens)")

text = st.text_area(
    "Cole um trecho em inglês",
    height=150,
    placeholder="Example: The quick brown fox jumps over the lazy dog.",
    help="Tradução instantânea para testes rápidos"
)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Traduzir", type="secondary", use_container_width=True):
        if text.strip():
            with st.spinner("Traduzindo..."):
                try:
                    payload = {"text": text}
                    r = requests.post(f"{API_URL}/translate/sync", json=payload, timeout=30)
                    
                    if r.status_code == 200:
                        result = r.json()
                        st.success("✅ Tradução concluída!")
                        st.markdown("### 📝 Resultado:")
                        st.info(result["translated"])
                        
                        with st.expander("🔍 Detalhes técnicos"):
                            st.json(result)
                    else:
                        st.error(f"❌ Erro {r.status_code}: {r.text}")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
        else:
            st.warning("⚠️ Por favor, insira algum texto para traduzir")

st.divider()

# Footer
st.caption("LEXI AI v0.2.0 | Powered by Helsinki-NLP/opus-mt-en-pt")