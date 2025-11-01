FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .

# Set environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "server.py"]

