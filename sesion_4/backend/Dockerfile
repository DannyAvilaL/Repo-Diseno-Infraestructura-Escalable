# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/app ./app
# Usuario no root (mínimo privilegio; compatible con runAsNonRoot en Kubernetes)
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin gateway
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request as u;u.urlopen('http://127.0.0.1:8000/healthz',timeout=2)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
