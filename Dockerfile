# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps for matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create data dirs
RUN mkdir -p data/prices data/alerts data/plots data/samples scripts src

COPY . .

ENV PORT=10000
# EXPOSE is optional on Render; keeping 10000 as a hint
EXPOSE 10000

# Default entrypoint: start via script to honor $PORT and avoid factory flag
RUN chmod +x scripts/start.sh
CMD ["bash", "-lc", "scripts/start.sh"]
