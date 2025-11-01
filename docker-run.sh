#!/bin/zsh
# Script to build and run the MCP server Docker image locally

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file from env.example and add your Reddit credentials."
    exit 1
fi

# Build the image
echo "Building Docker image..."
docker build -t reddit-mcp-server .

# Run the container
echo "Running container..."
docker run -it --rm --env-file .env reddit-mcp-server

