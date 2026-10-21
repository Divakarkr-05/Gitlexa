# Gitlexa Setup Script for Windows PowerShell
Write-Host "Setting up Gitlexa environment..." -ForegroundColor Cyan

if (Test-Path "backend") {
    Write-Host "Installing backend dependencies..."
    pip install -r backend/requirements.txt -r backend/requirements-dev.txt
}

if (Test-Path "frontend") {
    Write-Host "Installing frontend dependencies..."
    cd frontend; npm install; cd ..
}

Write-Host "Setup complete!" -ForegroundColor Green
