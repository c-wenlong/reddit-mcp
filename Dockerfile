FROM python:3.10-slim

WORKDIR /app

# Copy dependency files first (Smithery's build system checks for uv.lock, then pyproject.toml)
COPY pyproject.toml uv.lock* ./
COPY requirements.txt .

# Install dependencies (Smithery may handle this, but include as fallback)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "server.py"]

