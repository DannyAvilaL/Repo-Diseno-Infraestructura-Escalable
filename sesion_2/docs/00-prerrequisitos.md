# Prerrequisitos

## Conocimientos

Familiaridad con desarrollo de software, línea de comandos, HTTP/REST y conceptos generales de computación en la nube. No se requiere experiencia previa en infraestructura de LLM.

## Software

| Herramienta | Versión | Uso | Verificación |
| --- | --- | --- | --- |
| Ubuntu | 24.04 LTS (nativo o WSL2) | Sistema base | `lsb_release -a` |
| Python | 3.12 | Backend y SDKs | `python3.12 --version` |
| Node.js | 20 o superior | Frontend | `node --version` |
| Git | Reciente | Repositorio | `git --version` |
| Docker + Compose | Opcional | Alternativa de despliegue local | `docker compose version` |
| Ollama | Reciente | Inferencia local | `ollama --version` |
| Azure CLI (`az`) | Reciente | Laboratorios Azure | `az version` |
| Google Cloud CLI (`gcloud`) | Reciente | Laboratorios Google Cloud | `gcloud version` |
| AWS CLI v2 (`aws`) | Reciente | Laboratorios AWS | `aws --version` |

## Hardware

Mínimo 8 GB de RAM y 10 GB libres de disco. No se requiere GPU. Ver la tabla de modelos en `labs/00-local-ollama/README.md`.

## Cuentas

Cuentas trial personales de Azure, Google Cloud y AWS, creadas la semana de cada bloque (ver `03-costos-y-limpieza.md`).
