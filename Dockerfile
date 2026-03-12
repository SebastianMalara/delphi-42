FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libzim-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /workspace/
COPY bot /workspace/bot
COPY core /workspace/core
COPY ingest /workspace/ingest
COPY scripts /workspace/scripts
COPY sample_data /workspace/sample_data
COPY config /workspace/config

RUN pip install --no-cache-dir -e .[bot,llm,zim]

CMD ["python", "-m", "bot.oracle_bot"]
