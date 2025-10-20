FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY config.json .

# Create necessary directories
RUN mkdir -p logs output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Brussels

# Run the optimizer
CMD ["python", "main.py"]
