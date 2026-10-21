#!/usr/bin/env bash
echo "Starting backend and frontend..."
(cd backend && uvicorn app.main:app --reload --port 8000) &
(cd frontend && npm run dev) &
wait
