# Ollama con modelo embebido en la imagen => arranque sin descarga (trade-off: imagen grande, build lento).
FROM ollama/ollama:latest
ENV OLLAMA_HOST=0.0.0.0:8080 OLLAMA_KEEP_ALIVE=-1 OLLAMA_MODELS=/models
ARG MODEL=llama3.2:1b
RUN ollama serve & sleep 5 && ollama pull ${MODEL} && pkill ollama || true
EXPOSE 8080
ENTRYPOINT ["ollama", "serve"]
