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
    echo "SEED_DATA is enabled. Waiting for API server to be ready..."
    
    # Wait for the API server to be ready
    timeout=60
    count=0
    while [ $count -lt $timeout ]; do
        if curl -f http://localhost:30000/v1/version > /dev/null 2>&1; then
            echo "API server is ready. Starting database seeding..."
            break
        fi
        echo "Waiting for API server... ($count/$timeout)"
        sleep 2
        count=$((count + 2))
    done
    
    if [ $count -ge $timeout ]; then
        echo "ERROR: API server failed to start within $timeout seconds"
        exit 1
    fi
    
    # Run seed data script
    uv run python scripts/seed_data.py
else
    echo "SEED_DATA is disabled. Skipping database seeding."
fi

# Wait for the application process
wait $APP_PID