FROM python:3.11-slim


RUN useradd -m appuser
WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app/ ./app


RUN mkdir -p /data && chown appuser /data
USER appuser


EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]