# PDF Processor Dockerfile

FROM python:3.11-slim

# Install poppler-utils for PDF processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt')"

# Set up entrypoint
ENTRYPOINT ["python", "ingest.py"]
