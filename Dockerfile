FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --compile -r requirements.txt \
    && find /usr/local/lib/python3.11 -name '*.pyc' -delete \
    && find /usr/local/lib/python3.11 -name '__pycache__' -type d -delete

# Copy application code
COPY . .

# Install the package in editable mode
RUN pip install -e .

# Expose port
EXPOSE 8000

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the application
CMD ["python", "main.py"]
