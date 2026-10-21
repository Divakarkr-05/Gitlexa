#!/usr/bin/env bash
set -e
echo "Setting up Gitlexa environment..."

if [ -d "backend" ]; then
    echo "Installing backend dependencies..."
    pip install -r backend/requirements.txt -r backend/requirements-dev.txt
fi

if [ -d "frontend" ]; then
    echo "Installing frontend dependencies..."
    (cd frontend && npm install)
fi

echo "Setup complete!"
