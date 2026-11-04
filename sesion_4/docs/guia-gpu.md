# Guía breve: GPU en laboratorio (opcional)

1. Ubuntu 24.04: `sudo ubuntu-drivers install` y reinicie; verifique con `nvidia-smi`.
2. Docker + NVIDIA Container Toolkit (siga la guía oficial de NVIDIA para su versión); pruebe `docker run --rm --gpus all ubuntu nvidia-smi`.
3. Compose: agregue al servicio `ollama` un bloque `deploy.resources.reservations.devices` con `driver: nvidia`, `count: 1`, `capabilities: [gpu]`.
4. Kubernetes: instale NVIDIA GPU Operator o el driver DRA según su versión (≥ 1.34 para DRA GA) y aplique `k8s/overlays/gpu`.
5. Verifique que Ollama usa GPU en sus logs de arranque. **Compare tokens/s CPU vs GPU con `loadtest.py` y registre sus propios resultados.**
Advertencia: no combine device plugin y DRA en el mismo nodo (sobre-admisión de GPU).
