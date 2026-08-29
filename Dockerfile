# Use official Python runtime as base image
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . .

# Create streamlit config directory
RUN mkdir -p ~/.streamlit

# Expose port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]