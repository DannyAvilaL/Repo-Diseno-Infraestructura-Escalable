# Entorno Ubuntu 24.04 / WSL2

## Opción A · WSL2 en Windows

```powershell
# PowerShell como administrador
wsl --install -d Ubuntu-24.04
wsl -l -v          # verificar VERSION = 2
```

Reinicie y abra «Ubuntu 24.04». Trabaje dentro del sistema de archivos de Linux (`~/`), no en `/mnt/c`, por rendimiento.

## Paquetes base

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install build-essential git curl unzip ca-certificates python3.12 python3.12-venv python3-pip
```

## Node.js 20+

Use el gestor de versiones de su preferencia (por ejemplo, `nvm`) o los paquetes oficiales de NodeSource; verifique con `node --version`.

## Docker (opcional)

En WSL2 se recomienda Docker Desktop con integración WSL activada; en Ubuntu nativo, siga la guía oficial de instalación de Docker Engine para Ubuntu. Verifique con `docker run --rm hello-world`.

## CLIs cloud

Instale `az`, `gcloud` y `aws` siguiendo la documentación oficial de cada proveedor y autentíquese con identidad, no con claves en archivos:

```bash
az login
gcloud auth login && gcloud auth application-default login
aws configure sso
```

## Verificación del entorno

```bash
python3.12 --version && node --version && git --version
cd llm-infra-escalable && make install && make test
```
