FROM python:3.11-slim


# Cria usuário não-root
RUN useradd -m appuser


WORKDIR /app


# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copia código
COPY app/ ./app


# ← CORREÇÃO: Cria /data com ownership ANTES de trocar usuário
RUN mkdir -p /data && chown -R appuser:appuser /data


# Muda para usuário não-root
USER appuser


EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]