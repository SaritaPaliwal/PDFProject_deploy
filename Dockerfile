# -----------------------------
# Stage 1: Base image
# -----------------------------
FROM python:3.11-slim   # Base image (Python 3.11 slim version)

# -----------------------------
# Stage 2: Environment settings
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1   # Prevents Python from writing .pyc files
ENV PYTHONUNBUFFERED=1          # Ensures logs are shown directly in terminal

# Set default working directory
WORKDIR /app   # This is where your code will be copied inside container

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
# Copy the whole project folder into /app
COPY . .

# IMPORTANT: change working directory to where manage.py is located
# Your manage.py path: D:\PDFProject\djangodemo\project\manage.py
# So inside container it will be: /app/djangodemo/project
WORKDIR /app/PDFhub

# -----------------------------
# Stage 6: Run Django app
# -----------------------------
# Run Django server (port 8000)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
