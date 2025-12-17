# -----------------------------
# Stage 1: Base image
# -----------------------------
# FROM nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085/2401067/python:3.11-slim
FROM mirror.gcr.io/library/python:3.11-slim

# FROM python:3.11-slim

# -----------------------------
# Stage 2: Environment settings
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# -----------------------------
# Stage 3: System dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    ghostscript \
    poppler-utils \
    pdftk-java \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    pkg-config \
    libhdf5-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Stage 4: Python dependencies
# -----------------------------
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Stage 5: Project files
# -----------------------------
COPY . /app/

# -----------------------------
# Stage 6: Expose & run
# -----------------------------
EXPOSE 8000

# Development (switch to gunicorn for prod)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "project.wsgi:application"]