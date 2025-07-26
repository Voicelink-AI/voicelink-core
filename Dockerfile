FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Build C++ extensions if needed
RUN if [ -f "audio_engine/CMakeLists.txt" ]; then \
    cd audio_engine && mkdir -p build && cd build && \
    cmake .. && make -j$(nproc); \
    fi

# Create directories
RUN mkdir -p temp logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
