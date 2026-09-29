# python:3.11-slim digest pinned by the Phase 0 build.
FROM python:3.11-slim@sha256:e41613d42d4891e4930f79523f93f81bbc7632584ec65e36ab055f41a800b41e AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM base AS runtime

RUN useradd --create-home --uid 10001 ulpf
RUN mkdir -p /data/storage /data/spool && chown -R ulpf:ulpf /app /data

ENV ULPF_STORAGE_DIR=/data/storage \
    ULPF_SPOOL_DIR=/data/spool \
    ULPF_API_PORT=8000 \
    ULPF_UDP_PORT=5514 \
    ULPF_POLL_INTERVAL=1.0 \
    ULPF_LOG_LEVEL=INFO

USER ulpf
VOLUME ["/data/storage", "/data/spool"]
EXPOSE 8000/tcp 5514/udp 5514/tcp
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "cli.main", "serve"]

FROM base AS test

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
CMD ["python", "-m", "pytest", "-q"]
