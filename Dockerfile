FROM python:3.11-slim
WORKDIR /app

RUN useradd --create-home --uid 10001 ulpf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/storage_data /app/spool && chown -R ulpf:ulpf /app

ENV ULPF_STORAGE_DIR=/app/storage_data \
    ULPF_SPOOL_DIR=/app/spool \
    ULPF_API_PORT=8000 \
    ULPF_UDP_PORT=5514 \
    ULPF_LOG_LEVEL=INFO

USER ulpf
VOLUME ["/app/storage_data", "/app/spool"]
EXPOSE 8000/tcp 5514/udp

HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "cli.main", "serve"]
