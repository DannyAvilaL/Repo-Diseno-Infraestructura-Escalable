# Imagen única para el gateway y las regiones simuladas. Usuario no root, sin secretos.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY scripts/mock_region.py ./scripts/mock_region.py
RUN useradd --create-home --uid 10001 appuser && mkdir -p /srv/data && chown appuser /srv/data
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz').status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
