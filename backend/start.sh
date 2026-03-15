#!/bin/bash

# OpenAgentRAG Backend Startup Script

set -e

echo "Starting OpenAgentRAG Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration before running again."
    exit 1
fi

# Check if Poetry is installed
if command -v poetry &> /dev/null; then
    echo "Using Poetry..."
    poetry install
    poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Poetry not found. Using pip..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt

    # Run application
    echo "Starting application..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi
