FROM python:3.13-slim
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && apt-get update && apt-get install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked
COPY app_simulator/ app_simulator/
COPY ingestion/ ingestion/
RUN crontab ingestion/crontab
ENV PYTHONUNBUFFERED=1
