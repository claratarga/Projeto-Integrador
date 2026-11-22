FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements-backend.txt .

RUN pip install --no-cache-dir -r requirements-backend.txt

COPY backend/ /app/backend/
COPY database/ /app/database/

ENV HOST=0.0.0.0
ENV PORTA=8000
ENV STORAGE_DIR=/app/backend/storage
ENV MODELO_PESOS=/app/backend/modelos/detector_v1.pt

EXPOSE 8000

CMD ["python", "docker-entrypoint.py"]
