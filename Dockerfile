FROM python:3.11-slim
WORKDIR /app
COPY simple_ulpf.py sources.json ./
RUN mkdir /data
VOLUME ["/data"]
ENTRYPOINT ["python", "simple_ulpf.py", "--output", "/data"]
CMD ["--help"]
