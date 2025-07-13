#!/bin/bash

# Startup script for Travel Planner Backend

echo "Starting Travel Planner Backend..."

# Check if required environment variables are set
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "Warning: JWT_SECRET_KEY not set, using default"
fi

if [ -z "$FIREBASE_CREDENTIALS_PATH" ]; then
    echo "Warning: No Firebase credentials provided"
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "Warning: GEMINI_API_KEY not set"
fi

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "Warning: GOOGLE_MAPS_API_KEY not set"
fi

# Start the application
exec uvicorn app:app --host 0.0.0.0 --port 8000 --log-level info 