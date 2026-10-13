# Despliegue de LOC-01 en Kubernetes (extensión avanzada)

Manifiestos para llevar el laboratorio local a un clúster (AKS, GKE, EKS o local con kind/minikube). Ilustran las decisiones de la Unidad C: réplicas repartidas entre zonas, sondas de salud ligadas a `/healthz` y `/readyz`, mínimo privilegio en los contenedores y NetworkPolicy de denegación por defecto.

| Archivo | Contenido |
| --- | --- |
| `00-namespace.yaml` | Namespace con Pod Security Standards `restricted` |
| `10-ollama.yaml` | Ollama con volumen persistente para modelos, Service interno |
| `20-backend.yaml` | ConfigMap, Deployment con 2 réplicas y dispersión por zona, Service, PodDisruptionBudget, HPA |
| `30-networkpolicy.yaml` | Denegación por defecto; solo el backend llega a Ollama |

## Validación realizada

Los manifiestos se validaron con `kubeconform` 0.8.0 en modo estricto contra los esquemas de Kubernetes 1.31 (13-oct-2026). **No se aplicaron a un clúster real.**

```bash
kubeconform -strict -summary -kubernetes-version 1.31.0 k8s/
```

## Uso

```bash
docker build -t <registro>/asistente-backend:1.0.0 ../backend && docker push <registro>/asistente-backend:1.0.0
sed -i 's#REGISTRO/asistente-backend:1.0.0#<registro>/asistente-backend:1.0.0#' 20-backend.yaml
kubectl apply -f .
kubectl -n asistente exec deploy/ollama -- ollama pull qwen2.5:1.5b
kubectl -n asistente port-forward svc/backend 8000:80
curl -s http://127.0.0.1:8000/readyz
```

Requisitos: un CNI que aplique NetworkPolicy (Calico, Cilium o el del proveedor). El controlador de ingress no está incluido; ajuste la etiqueta de namespace en `30-networkpolicy.yaml`.

## Decisiones y limitaciones

- **Ollama con una réplica y volumen RWO**: no es alta disponibilidad. Es la forma más sencilla de mostrar el serving en el clúster; para HA de serving se necesitan réplicas con almacenamiento de pesos compartido o precargado (Unidad C).
- **HPA por CPU** es una aproximación: en inferencia, escalar por longitud de cola o por TTFT es más fiel a la experiencia del usuario.
- **Sistema de archivos de solo lectura** en el backend: posible porque la aplicación no escribe en disco.

## Limpieza

```bash
kubectl delete namespace asistente
```
