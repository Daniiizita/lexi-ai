import time
import os
import glob
from pathlib import Path
from .router import get_translator

# DESCOMENTAR PARA DOCKER
# STORAGE_DIR = os.environ.get("STORAGE_DIR", "/data")

# local abaixo
STORAGE_DIR = os.environ.get("STORAGE_DIR", "./storage")
Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)

def process_pending_jobs():
    """
    Worker que processa arquivos pendentes de tradução.
    Monitora STORAGE_DIR em busca de arquivos .pending
    """
    translator = get_translator()  # Carrega modelo uma vez
    
    print(f"🔄 Worker iniciado. Monitorando: {STORAGE_DIR}")
    
    while True:
        pending_files = glob.glob(os.path.join(STORAGE_DIR, "*.pending"))
        
        for pending_file in pending_files:
            try:
                # Remove extensão .pending para obter arquivo original
                original_file = pending_file[:-8]
                
                # Lê configuração de tradução
                with open(pending_file, "r") as f:
                    target_lang = f.read().strip()
                
                # Lê conteúdo original
                # TODO: Adicionar suporte para PDF/EPUB com pypdf2/ebooklib
                with open(original_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                print(f"📖 Traduzindo: {original_file}")
                translated = translator.translate(content)
                
                # Salva tradução
                output_file = f"{original_file}.{target_lang}.translated.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(translated)
                
                # Remove flag de pending
                os.remove(pending_file)
                print(f"✅ Concluído: {output_file}")
                
            except Exception as e:
                print(f"❌ Erro ao processar {pending_file}: {e}")
                # Opcional: mover para pasta de erros
        
        time.sleep(5)


if __name__ == "__main__":
    process_pending_jobs()