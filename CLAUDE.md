# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python/FastAPI)

```bash
# Install dependencies

cd backend && uv sync

# Run linting and type checking
ruff check .
mypy .

# Run tests (Docker Compose)

docker-compose exec backend pytest

# Run tests (Kubernetes)

kubectl exec -it service/test-observer-api -- pytest

# Database migrations (Docker Compose)

docker-compose exec backend alembic revision --autogenerate -m "Description"
docker-compose exec backend alembic upgrade head

# Database migrations (Kubernetes)

kubectl exec -it service/test-observer-api -- alembic revision --autogenerate -m "Description"
kubectl exec -it service/test-observer-api -- alembic upgrade head

# Seed database with test data (Docker Compose)

docker-compose exec backend python scripts/seed_data.py

# Seed database with test data (Kubernetes)

kubectl exec -it service/test-observer-api -- python scripts/seed_data.py
```

### Frontend (Flutter/Dart)

```bash
# Install dependencies

cd frontend && flutter pub get

# Generate code (required before running)
dart run build_runner build

# Run application (development with hot reload)
flutter run -d chrome --web-experimental-hot-reload

# Build for production (with WASM)
flutter build web --wasm

# Run tests
flutter analyze
flutter test --platform chrome

# Run integration tests
./run_integration_tests.sh
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
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Execute commands in running containers
docker-compose exec backend bash
docker-compose exec frontend bash
```

#### Kubernetes (Alternative)

```bash
# Start microk8s development
skaffold dev --no-prune=false --cache-artifacts=false
```

**Docker Compose Services:**

- `backend`: FastAPI server on port 30000
- `frontend`: Flutter web app on port 8080  
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

- **Framework**: Flutter web application with Riverpod state management
- **Entry Point**: `frontend/lib/main.dart`
- **Navigation**: Router-based SPA with family-specific routes (snaps, debs, charms, images)
- **State Management**: Riverpod providers for API state and caching
- **API Communication**: HTTP REST calls via Dio client through `ApiRepository`

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

### Code Generation (Frontend)

- Flutter uses code generation for models and providers
- Always run `dart run build_runner build` after model changes
- Generated files (`.g.dart`, `.freezed.dart`) are committed to version control

### Testing Approach

- Backend: pytest within Docker containers or Kubernetes pods
- Frontend: Chrome-based unit tests and integration tests
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