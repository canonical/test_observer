#!/bin/bash
set -e

echo "Starting Test Observer Backend..."

# Run database migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
uv run uvicorn test_observer.main:app --host 0.0.0.0 --port 30000 --reload &

# Get the PID of the uvicorn process
APP_PID=$!

# Check if seeding is enabled (default to false)
if [ "${SEED_DATA:-false}" = "true" ]; then
    echo "SEED_DATA is enabled. Checking if seeding is needed..."
    
    # Run seed data script
    uv run python scripts/seed_data.py
else
    echo "SEED_DATA is disabled. Skipping database seeding."
fi

# Wait for the application process
wait $APP_PID