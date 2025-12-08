import streamlit as st
import requests
import os
import time
from typing import List, Dict


# Prioriza variável de ambiente, depois secrets, depois fallback local
API_URL = os.getenv("API_URL") or st.secrets.get("API_URL", "http://localhost:8000")


st.set_page_config(
    page_title="LEXI AI - Tradução Literária",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .metric-card h4 {
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    .metric-card code {
        display: block;
        padding: 0.5rem;
        background-color: #ffffff;
        border-radius: 0.25rem;
        font-size: 0.85rem;
        word-break: break-all;
    }
    /* CSS para cards de métricas customizados */
    .custom-metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .custom-metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .custom-metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .custom-metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f1f1f;
    }
    /* Previne quebra de layout em expanders */
    .streamlit-expanderContent {
        overflow-x: auto;
    }
    /* Expander com título completo visível */
    .streamlit-expanderHeader {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📚 LEXI AI — Tradução Literária Profissional")
st.caption("Traduza livros do inglês para português-Brasil com GPU-accelerated AI")

# Sidebar com status e configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Status da API
    st.subheader("🔌 Status da API")
    try:
        health = requests.get(f"{API_URL}/health", timeout=2)
        if health.status_code == 200:
            data = health.json()
            st.success("✅ API Online")
            
            # Métricas formatadas com HTML customizado
            model_short = data.get("model_name", "N/A").split('/')[-1]
            
            metrics_html = f"""
            <div class="custom-metric-grid">
                <div class="custom-metric-card">
                    <div class="custom-metric-label">Ambiente</div>
                    <div class="custom-metric-value" style="font-size: 1.2rem;">{data.get("environment", "N/A")}</div>
                </div>
                <div class="custom-metric-card">
                    <div class="custom-metric-label">Modelo</div>
                    <div class="custom-metric-value" style="font-size: 1rem;">{model_short}</div>
                </div>
            </div>
            """
            st.markdown(metrics_html, unsafe_allow_html=True)
            
            # Expander com detalhes técnicos
            with st.expander("🔍 Detalhes técnicos"):
                st.json(data)
        else:
            st.error("❌ API com problemas")
    except Exception as e:
        st.error("❌ API offline")
        st.caption(f"Erro: {str(e)[:50]}")
        st.info("💡 Inicie a API:\n```bash\ncd translator\nuvicorn app.main:app --reload\n```")
    
    st.divider()
    
    # Configurações de tradução
    st.subheader("🎛️ Configurações de Tradução")
    batch_size = st.slider(
        "Batch Size",
        min_value=4,
        max_value=32,
        value=16,
        step=4,
        help="Maior = mais rápido (requer mais VRAM)"
    )
    
    preserve_formatting = st.checkbox(
        "Preservar formatação",
        value=True,
        help="Mantém negrito, itálico, etc."
    )
    
    show_technical_details = st.checkbox(
        "Mostrar detalhes técnicos",
        value=False
    )

# Tabs principais
tab1, tab2, tab3 = st.tabs(["📤 Upload de Livro", "⚡ Teste Rápido", "📊 Batch Processing"])

# TAB 1: Upload de Livro
with tab1:
    st.subheader("📤 Upload de Livro Completo")
    st.caption("Suporta: TXT, PDF, EPUB (processamento assíncrono via worker)")
    
    uploaded = st.file_uploader(
        "Selecione o arquivo",
        type=["txt", "pdf", "epub"],
        help="O arquivo será processado em segundo plano"
    )
    
    if uploaded is not None:
        # Métricas do arquivo com HTML customizado
        file_size_mb = uploaded.size / (1024 * 1024)
        
        file_metrics_html = f"""
        <div class="custom-metric-grid">
            <div class="custom-metric-card">
                <div class="custom-metric-label">📁 Arquivo</div>
                <div class="custom-metric-value" style="font-size: 1rem;">{uploaded.name}</div>
            </div>
            <div class="custom-metric-card">
                <div class="custom-metric-label">💾 Tamanho</div>
                <div class="custom-metric-value">{file_size_mb:.2f} MB</div>
            </div>
            <div class="custom-metric-card">
                <div class="custom-metric-label">📝 Tipo</div>
                <div class="custom-metric-value">{uploaded.type}</div>
            </div>
        </div>
        """
        st.markdown(file_metrics_html, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            target_lang = st.selectbox("Idioma de destino", ["pt-BR", "pt"], index=0)
        
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
                        
                        # Card com job ID usando HTML customizado
                        job_card_html = f"""
                        <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 0.5rem; padding: 1.5rem; margin: 1rem 0;">
                            <h4 style="color: #155724; margin-bottom: 1rem;">✅ Job Criado</h4>
                            <div style="background: white; padding: 0.75rem; border-radius: 0.25rem; margin-bottom: 0.5rem;">
                                <strong>Job ID:</strong><br/>
                                <code style="font-size: 0.9rem; word-break: break-all;">{job['job_id']}</code>
                            </div>
                            <div style="margin-top: 0.5rem;">
                                <strong>Status:</strong> <span style="color: #856404; background: #fff3cd; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{job.get('status', 'pending')}</span>
                            </div>
                        </div>
                        """
                        st.markdown(job_card_html, unsafe_allow_html=True)
                        
                        st.info("💡 O worker está processando em segundo plano. Resultado em `storage/`")
                    else:
                        st.error(f"❌ Erro {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"❌ Erro ao enviar: {e}")

# TAB 2: Teste Rápido
with tab2:
    st.subheader("⚡ Teste Rápido (Tradução Individual)")
    st.caption("Para trechos pequenos (≤512 tokens)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🇬🇧 Original (Inglês)**")
        text = st.text_area(
            "Cole o texto",
            height=200,
            placeholder="The quick brown fox jumps over the lazy dog.",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("**🇧🇷 Traduzido (Português)**")
        translation_placeholder = st.empty()
    
    if st.button("🔄 Traduzir", type="primary", use_container_width=True):
        if text.strip():
            with st.spinner("Traduzindo..."):
                start_time = time.time()
                try:
                    payload = {"text": text}
                    r = requests.post(f"{API_URL}/translate/sync", json=payload, timeout=30)
                    elapsed = time.time() - start_time
                    
                    if r.status_code == 200:
                        result = r.json()
                        
                        # Mostra tradução
                        with translation_placeholder:
                            st.text_area(
                                "Tradução",
                                value=result["translated"],
                                height=200,
                                label_visibility="collapsed"
                            )
                        
                        # Métricas de performance com HTML customizado
                        st.markdown("---")
                        word_count = len(text.split())
                        char_count = len(text)
                        
                        metrics_html = f"""
                        <div class="custom-metric-grid">
                            <div class="custom-metric-card">
                                <div class="custom-metric-label">⏱️ Tempo</div>
                                <div class="custom-metric-value">{elapsed:.2f}s</div>
                            </div>
                            <div class="custom-metric-card">
                                <div class="custom-metric-label">📝 Palavras</div>
                                <div class="custom-metric-value">{word_count}</div>
                            </div>
                            <div class="custom-metric-card">
                                <div class="custom-metric-label">🔤 Caracteres</div>
                                <div class="custom-metric-value">{char_count}</div>
                            </div>
                            <div class="custom-metric-card">
                                <div class="custom-metric-label">🚀 Taxa</div>
                                <div class="custom-metric-value">{word_count/elapsed:.1f} pal/s</div>
                            </div>
                        </div>
                        """
                        st.markdown(metrics_html, unsafe_allow_html=True)
                        
                        # Detalhes técnicos (opcional)
                        if show_technical_details:
                            with st.expander("🔍 Detalhes técnicos"):
                                st.json(result)
                    else:
                        st.error(f"❌ Erro {r.status_code}: {r.text}")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
        else:
            st.warning("⚠️ Digite algum texto para traduzir")

# TAB 3: Batch Processing
with tab3:
    st.subheader("📊 Batch Processing (Alta Performance)")
    st.caption("Traduza múltiplos textos simultaneamente (até 40x mais rápido)")
    
    # Input de textos
    st.markdown("**📥 Textos de Entrada (um por linha)**")
    batch_input = st.text_area(
        "Cole os textos",
        height=200,
        placeholder="The quick brown fox...\nMachine learning is...\nBooks are portals...",
        label_visibility="collapsed"
    )
    
    if st.button("🚀 Traduzir Batch", type="primary", use_container_width=True):
        if batch_input.strip():
            # Processa entrada
            texts = [t.strip() for t in batch_input.split('\n') if t.strip()]
            
            if texts:
                st.info(f"📊 Processando {len(texts)} textos...")
                
                # Prepara chunks seguindo o formato LEXI
                chunks = [
                    {
                        "chunk_id": str(i),
                        "plain_text": text,
                        "inline_markup": "",
                        "context_before": "",
                        "context_after": "",
                        "glossary": "",
                        "style_guide": ""
                    }
                    for i, text in enumerate(texts)
                ]
                
                # Barra de progresso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Traduzindo em batch..."):
                    start_time = time.time()
                    try:
                        response = requests.post(
                            f"{API_URL}/translate/batch",
                            json=chunks,
                            timeout=60
                        )
                        elapsed = time.time() - start_time
                        
                        if response.status_code == 200:
                            results = response.json()
                            progress_bar.progress(100)
                            status_text.success("✅ Tradução concluída!")
                            
                            # Métricas com HTML customizado
                            st.markdown("---")
                            
                            total_chars = sum(len(t) for t in texts)
                            speedup = (len(texts) * 0.5) / elapsed
                            
                            metrics_html = f"""
                            <div class="custom-metric-grid">
                                <div class="custom-metric-card">
                                    <div class="custom-metric-label">⏱️ Tempo</div>
                                    <div class="custom-metric-value">{elapsed:.2f}s</div>
                                </div>
                                <div class="custom-metric-card">
                                    <div class="custom-metric-label">📊 Textos</div>
                                    <div class="custom-metric-value">{len(texts)}</div>
                                </div>
                                <div class="custom-metric-card">
                                    <div class="custom-metric-label">🔤 Caracteres</div>
                                    <div class="custom-metric-value">{total_chars:,}</div>
                                </div>
                                <div class="custom-metric-card">
                                    <div class="custom-metric-label">🚀 Taxa</div>
                                    <div class="custom-metric-value">{len(texts)/elapsed:.1f} trad/s</div>
                                </div>
                                <div class="custom-metric-card">
                                    <div class="custom-metric-label">⚡ Speedup</div>
                                    <div class="custom-metric-value">{speedup:.1f}x</div>
                                </div>
                            </div>
                            """
                            st.markdown(metrics_html, unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Resultados com títulos completos
                            st.markdown("### 📤 Resultados")
                            
                            for i, (original, result) in enumerate(zip(texts, results)):
                                # Título completo sem truncamento
                                expander_title = f"**Texto {i+1}:** {original[:80]}"
                                if len(original) > 80:
                                    expander_title += "..."
                                
                                with st.expander(expander_title, expanded=False):
                                    col_res1, col_res2 = st.columns(2)
                                    with col_res1:
                                        st.markdown("**🇬🇧 Original:**")
                                        st.markdown(f"```\n{original}\n```")
                                    with col_res2:
                                        st.markdown("**🇧🇷 Traduzido:**")
                                        st.markdown(f"```\n{result.get('translated_html', result.get('translated', 'N/A'))}\n```")
                                    
                                    # Mostra decisões de tradução se disponível
                                    if show_technical_details and result.get('decisions'):
                                        st.markdown("**📋 Decisões de Tradução:**")
                                        for decision in result.get('decisions', []):
                                            st.caption(f"• {decision}")
                            
                            # Download dos resultados
                            st.markdown("---")
                            
                            translations_text = "\n\n" + "="*80 + "\n\n"
                            translations_text += "LEXI AI - Resultados de Tradução em Batch\n"
                            translations_text += f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            translations_text += f"Total de textos: {len(texts)}\n"
                            translations_text += f"Tempo: {elapsed:.2f}s | Taxa: {len(texts)/elapsed:.1f} trad/s\n"
                            translations_text += f"Speedup: {speedup:.1f}x\n"
                            translations_text += "="*80 + "\n\n"
                            
                            for i, (orig, res) in enumerate(zip(texts, results)):
                                translations_text += f"\n--- TEXTO {i+1} ---\n\n"
                                translations_text += f"Original (EN):\n{orig}\n\n"
                                translations_text += f"Traduzido (PT-BR):\n{res.get('translated_html', res.get('translated', 'N/A'))}\n"
                                translations_text += "\n" + "-"*80 + "\n"
                            
                            st.download_button(
                                label="💾 Download resultados (.txt)",
                                data=translations_text,
                                file_name=f"lexi_batch_{int(time.time())}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                            
                        else:
                            st.error(f"❌ Erro {response.status_code}: {response.text}")
                            
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
                        import traceback
                        if show_technical_details:
                            st.code(traceback.format_exc())
            else:
                st.warning("⚠️ Nenhum texto válido encontrado")
        else:
            st.warning("⚠️ Cole textos para traduzir")

# Footer
st.divider()
col_footer1, col_footer2, col_footer3 = st.columns([2, 1, 1])
with col_footer1:
    st.caption("LEXI AI v1.0.0 | Powered by Helsinki-NLP")
with col_footer2:
    if st.button("📖 Documentação"):
        st.markdown("[GitHub](https://github.com/Daniiizita/lexi-ai)")
with col_footer3:
    if st.button("🐛 Reportar Bug"):
        st.markdown("[Issues](https://github.com/Daniiizita/lexi-ai/issues)")