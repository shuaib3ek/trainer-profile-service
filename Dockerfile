# Use stable Debian Bookworm base (not rolling Trixie)
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies for WeasyPrint + build tools for cffi/cairocffi
RUN apt-get update && apt-get install -y \
    build-essential \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi-dev \
    fonts-dejavu-core \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (pinned versions)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

EXPOSE 8000

# Launch FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]