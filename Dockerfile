FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for pandas/numpy compilation)
# RUN apt-get update && apt-get install -y gcc

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary source directories
COPY src/ ./src/
COPY backend/ ./backend/

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
