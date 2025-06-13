#!/bin/bash
set -e

echo "Starting Test Observer Backend..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
uv run python wait_for_db.py

# Run database migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
uv run uvicorn test_observer.main:app --host 0.0.0.0 --port 30000 --reload &

# Get the PID of the uvicorn process
APP_PID=$!

# Wait for the application to be ready
echo "Waiting for application to be ready..."
uv run python wait_for_app.py

# Check if seeding is enabled (default to true for development)
if [ "${SEED_DATA:-true}" = "true" ]; then
    echo "Seeding database with test data..."
    
    # Run seed data script
    if uv run python scripts/seed_data.py; then
        echo "Database seeding completed successfully"
    else
        echo "Database seeding failed, but continuing..."
    fi
fi

# Wait for the application process
wait $APP_PID