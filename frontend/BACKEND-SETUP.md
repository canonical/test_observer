# Running the Backend

## Known Issue: Docker Build in CI Environment

The backend Docker image build fails in GitHub Actions CI environment due to network timeouts when downloading Python packages. This is a limitation of the GitHub Actions environment's network policies, not a problem with the code.

**Error example:**
```
× Failed to download `celery==5.5.1`
├─▶ Request failed after 3 retries
├─▶ error sending request for url
╰─▶ operation timed out
```

## How to Run the Backend Locally

The backend works perfectly when run locally. Follow these steps:

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available for Docker

### Steps

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/canonical/test_observer.git
   cd test_observer
   ```

2. **Start all services** (backend, database, SAML IDP):
   ```bash
   docker compose up
   ```

   This will:
   - Build the backend API image
   - Start PostgreSQL database
   - Start SAML identity provider
   - Run database migrations automatically
   - Seed the database with test data (by default)

3. **Wait for services to be healthy**:
   - Backend API will be available at `http://localhost:30000`
   - Check logs: `docker compose logs -f test-observer-api`

4. **Access the vanilla JS frontend**:
   ```bash
   # In a new terminal
   cd frontend
   python3 -m http.server 8080
   ```

   Then open `http://localhost:8080/index.html` in your browser

### Alternative: Run Backend Only

If you just want the backend without the Flutter frontend:

```bash
docker compose up test-observer-api test-observer-db saml-idp
```

### Verify Backend is Running

```bash
# Check service status
docker compose ps

# Test API endpoint
curl http://localhost:30000/v1/artefacts?family=snap
```

### Starting Fresh

To reset everything and start fresh:

```bash
# Stop and remove all containers and volumes
docker compose down -v

# Start again
docker compose up
```

### Without Seeding Data

If you don't want test data:

```bash
SEED_DATA=false docker compose up
```

## Using Mock Data (No Backend Required)

If you can't run the backend, the vanilla JS frontend includes a mock data mode for testing:

1. **Start the frontend**:
   ```bash
   cd frontend
   python3 -m http.server 8080
   ```

2. **Open with mock mode enabled**:
   ```
   http://localhost:8080/index.html?mock=true
   ```

This will load sample data so you can see the UI working without needing the backend.

## Troubleshooting

### Port Already in Use

If port 30000 or 5432 is already in use:

```bash
# Check what's using the port
sudo lsof -i :30000
sudo lsof -i :5432

# Kill the process or stop the service
```

### Build Fails

If the Docker build fails locally:

1. Check your internet connection
2. Clear Docker cache: `docker system prune -a`
3. Try building with: `docker compose build --no-cache test-observer-api`

### Database Issues

If you see database connection errors:

```bash
# Check database logs
docker compose logs test-observer-db

# Restart database
docker compose restart test-observer-db
```

## Development Workflow

For active development:

```bash
# Run in background
docker compose up -d

# View logs
docker compose logs -f test-observer-api

# Restart after code changes
docker compose up --build test-observer-api

# Run tests
docker compose exec test-observer-api pytest

# Access database
docker compose exec test-observer-db psql -U test_observer_user -d test_observer_db
```

## Why This Works Locally But Not in CI

The GitHub Actions environment has:
- Strict network policies that block or rate-limit certain domains
- Timeouts for long-running operations
- Limited resources compared to local machines

When you run locally, your machine has:
- Normal internet access without restrictions
- Better network performance
- More resources available

This is a common issue with CI environments and is not a problem with the application code.
