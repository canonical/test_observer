# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python/FastAPI)

```bash
# Install dependencies

cd backend && uv sync

# Run linting and type checking
ruff check .
ruff format --check .
mypy .

# Run tests (Docker Compose)

docker compose exec backend pytest

# Run tests (Kubernetes)

kubectl exec -it service/test-observer-api -- pytest

# Run tests on host machine (requires Docker Compose running)

cd backend && uv run pytest

# Run tests with custom database URL

TEST_DB_URL="postgresql+pg8000://user:pass@host:port/db" uv run pytest

# Database migrations (Docker Compose)

docker compose exec backend alembic revision --autogenerate -m "Description"
docker compose exec backend alembic upgrade head

# Database migrations (Kubernetes)

kubectl exec -it service/test-observer-api -- alembic revision --autogenerate -m "Description"
kubectl exec -it service/test-observer-api -- alembic upgrade head

# Seed database with test data (Docker Compose)

docker compose exec backend python scripts/seed_data.py

# Seed database with test data (Kubernetes)

kubectl exec -it service/test-observer-api -- python scripts/seed_data.py
```

### Frontend (Vanilla JavaScript)

```bash
# No build step required! The frontend uses native ES6 modules.

# Serve the frontend locally for development
cd frontend && python3 -m http.server 8080
# Or use any other HTTP server:
# npx http-server -p 8080
# php -S localhost:8080

# Access at http://localhost:8080

# The frontend automatically connects to backend at http://localhost:30000/
# To use a different backend, set window.testObserverAPIBaseURI or modify js/config.js
```

### Development Environment

#### Docker Compose (Recommended)

```bash
# Start full stack with docker-compose (migrations and seeding run automatically)
docker compose up

# Start without seeding (set environment variable)
SEED_DATA=false docker compose up

# Run in background
docker compose up -d

# Rebuild containers after code changes
docker compose up --build

# Stop services
docker compose down

# View logs
docker compose logs -f [service-name]

# Execute commands in running containers
docker compose exec backend bash
docker compose exec frontend bash
```

#### Kubernetes (Alternative)

```bash
# Start microk8s development
skaffold dev --no-prune=false --cache-artifacts=false
```

**Docker Compose Services:**

- `backend`: FastAPI server on port 30000
- `frontend`: Vanilla JS web app served via nginx on port 30001
- `db`: PostgreSQL database with persistent volume
- Automatic migrations and seeding via `dev_entrypoint.sh`

## Architecture Overview

**Test Observer** is a dashboard for viewing and managing test results on software artefacts (debs, snaps, charms, images) across different environments. The system does not run tests itself, but provides APIs for reporting and reviewing test results.

### Backend Architecture

- **Framework**: FastAPI with SQLAlchemy ORM and PostgreSQL
- **Entry Point**: `backend/test_observer/main.py`
- **API Structure**: Versioned REST API (`/v1/*`) organized by domain:
  - `/artefacts` - Software package lifecycle management
  - `/test-executions` - Test execution workflow and results
  - `/environments` - Test environment management
  - `/reports` - Analytics and reporting
- **Data Access**: Repository pattern with `data_access/` module
- **Background Tasks**: Celery with Redis for async processing

### Frontend Architecture

- **Framework**: Vanilla JavaScript (ES6+ modules) with HTML and CSS
- **Entry Point**: `frontend/index.html` and `frontend/js/app.js`
- **Navigation**: Component-based SPA with routes for different artefact types (snaps, debs, charms, images)
- **Styling**: Vanilla Framework CSS with custom styles
- **Configuration**: Centralized config in `js/config.js` for artefact types and API settings
- **Components**: Modular JavaScript classes in `js/components/` directory

### Core Data Model

The system centers around **Artefacts** (software packages) that go through testing workflows:

- **Artefact**: Central entity supporting multiple families (snap/deb/charm/image)
- **ArtefactBuild**: Architecture-specific builds with optional revisions
- **Environment**: Test execution environments (devices/containers)
- **TestExecution**: Links builds to environments, tracks test status
- **TestResult**: Individual test outcomes with logs and status
- **Review System**: Multi-level approval workflow for artefact releases

### Key Patterns

- **Domain-Driven Design**: Controllers organized by business domain, not HTTP verbs
- **Partial Unique Constraints**: Database handles different artefact family requirements
- **Event-Driven Architecture**: TestEvents provide audit trail of test execution
- **Soft Delete**: Uses `archived` field instead of physical deletion
- **External Integrations**: Launchpad API, Snapcraft API for artefact metadata

## Important Conventions

### Database Migrations

- Use Alembic for all schema changes
- Auto-generate migrations: `alembic revision --autogenerate -m "Description"`
- Always review generated migrations before applying
- Copy migrations from pod to host: `kubectl cp test-observer-api-POD:/home/app/migrations/versions ./migrations/versions`
- **Development Docker**: Migrations run automatically on container startup via `dev_entrypoint.sh`
- **Test Data Seeding**: Development Docker automatically seeds test data unless `SEED_DATA=false`

### Code Structure (Frontend)

- Frontend uses native ES6 modules - no build step required
- Components are organized in `js/components/` directory
- Configuration is centralized in `js/config.js`
- Custom CSS extends Vanilla Framework in `css/style.css`

### Testing Approach

- Backend: pytest within Docker containers or Kubernetes pods
- Frontend: Manual testing in browser (automated testing to be added in future PRs)
- Use existing test data generators in `tests/data_generator.py`
- Docker Compose: `docker-compose exec backend pytest`
- Kubernetes: `kubectl exec -it service/test-observer-api -- pytest`

### API Design

- All endpoints versioned with `/v1/` prefix
- RESTful resource-based routing
- Pydantic models for request/response validation
- Dependency injection for database sessions and auth

### Environment Configuration

- Development: microk8s + Skaffold (preferred) or docker-compose
- Database: PostgreSQL (local) or microk8s postgres
- Frontend connects to backend at `http://localhost:30000/` by default