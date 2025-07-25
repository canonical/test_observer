# Test Observer Backend

## Development Setup

This project supports [microk8s](https://microk8s.io/) development environment with the help of [Skaffold](https://skaffold.dev/). It also uses [uv](https://github.com/astral-sh/uv) for dependency management.

### 1. Install required tools

- Install [docker](https://docs.docker.com/engine/install/ubuntu/) and [setup permissions](https://docs.docker.com/engine/install/linux-postinstall/)
- Install [microk8s](https://microk8s.io/docs/getting-started) and setup permissions
- Install [Skaffold](https://skaffold.dev/docs/install/#standalone-binary)
- Install [uv](https://github.com/astral-sh/uv#installation)
- Install [pre-commit](https://pre-commit.com) (best done using `sudo apt install pre-commit`, followed by `pre-commit install` in the `backend` directory)
- Install [jq](https://github.com/jqlang/jq) (`sudo apt install jq`)

### 2. Setup Skaffold and microk8s

- Skaffold requires a k8s registry to push and pull images from so just run `$ microk8s enable registry`
- Allow pods to communicate together in microk8s through CoreDNS by running `$ microk8s enable dns`
- Allow persistent volume claims to claim storage using `$ microk8s enable hostpath-storage`
- Skaffold uses kubectl so create an alias for `microk8s.kubectl` using `snap alias microk8s.kubectl kubectl`
- In order for Skaffold to connect to microk8s it needs it's configuration, so run `$ microk8s config > ~/.kube/config`. Note that if you get an error connecting to the cluster, it could be that the cluster's IP has changed for some reason, so you have to run this command again

### 3. Install python dependencies for linting and completions

While technically not required to run the code, it helps to have dependencies installed on host system to get code completions and linting. To do that just run `$ uv sync`. Note that uv will create a virtual environment for you in the `.venv` directory.

Linting and formatting checks are done using ruff, and type checking using mypy. We have CI in place to make those checks, but it's probably a good idea to setup your editor to use these. Note that their settings are in `pyproject.toml`.

The project uses [pre-commit](https://pre-commit.com) to auto generate OpenAPI schema file. To set it up for your working copy of the repository:

```bash
sudo apt install pre-commit jq
pre-commit install # in the `backend` directory
```

### 4. Start the development environment

Assuming that your microk8s cluster is running, you can start the development environment by simply running `$ skaffold dev --no-prune=false --cache-artifacts=false`. This command will build the docker images and push them to your microk8s registry, then apply your k8s manifest to start the cluster and pull those images. Additionally, skaffold will watch for file changes and either sync them directly inside the running containers or rebuild and redeploy k8s cluster for you automatically.

### 5. [Optional] seed the database

Run `scripts/seed_data.py` script to seed the database with some dummy data. This can be useful when working with front-end. Note that this needs to run within the container.

`$ kubectl exec -it service/test-observer-api -- python scripts/seed_data.py`

## Dependency Management

### Add/Install dependency

`$ uv add foo`

If it's a dev dependency

`$ uv add --dev foo`

### Remove/Uninstall dependency

`$ uv remove foo`

## Database Migrations

The project uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) to manage database migrations. Migrations will be applied automatically when running Skaffold. But making changes to data models requires manually creating and applying migrations.

### Create Migrations

For more information on how to create migrations, please check [Alembic docs](https://alembic.sqlalchemy.org/en/latest/). Note, that it's worth noting that Alembic can help [auto generate migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) based on differences between SQLAlchemy ORMs and the actual database. But developers have to check these migrations to make sure they're fine. To generate migrations automatically though, just run:

`$ kubectl exec -it service/test-observer-api -- alembic revision --autogenerate -m "Migration description"`

Note however that this created migration will reside inside the pod not on your host machine. So you have to copy it over by:

`$ kubectl cp test-observer-api-RESTOFPODNAME:/home/app/migrations/versions ./migrations/versions`

You can get RESTOFPODNAME by running

`$ kubectl get pods`

### Applying Migrations

Since the database is in microk8s cluster, migrations have to be applied inside the cluster and not on the host machine. To do that we can just run the migrations on our api service which will run in one of the api pods through:

`$ kubectl exec -it service/test-observer-api -- alembic upgrade head`

## Tests

Tests can be run in several ways:

### Running tests in Kubernetes (Skaffold)

To run the tests in the Kubernetes environment, first make sure that you're running skaffold. Then execute the pytest command in the API pod:

`$ kubectl exec -it service/test-observer-api -- pytest`

### Running tests in Docker Compose

If you're using Docker Compose for development:

`$ docker compose exec test-observer-api pytest`

### Running tests on host machine

You can also run tests directly on your host machine if Docker Compose is running (exposing PostgreSQL on localhost:5432):

```bash
# First ensure dependencies are installed
$ uv sync --all-groups
$ uv pip install -e .

# Run tests
$ uv run pytest
```

The test configuration automatically detects whether to use localhost (for host machine testing) or the Docker service name (for container testing).

### Custom database configuration

You can override the database connection by setting the `TEST_DB_URL` environment variable:

`$ TEST_DB_URL="postgresql+pg8000://user:password@host:port/database" uv run pytest`

## OCI images

Two Dockerfiles are provided for the backend application:

- `backend/Dockerfile`: one to use for local development purposes, offering hot reloading.
- `backend/Dockerfile.production`: one to use for integration tests, staging, production deploys.

## Versioning

The application is versioned for release purposes using source control tag and commit metadata, using [uv-dynamic-versioning](https://pypi.org/project/uv-dynamic-versioning/).

The version "0.0.0" stated in the `pyproject.toml` is a "fallback version" which is returned by the `/version` endpoint when the application is either run:

1. ... directly from source, i.e. not built and launched as wheel.
2. ... using a wheel built with `uv build` when dynamic versioning is not configured.

## Building Docker images

There are two Docker images in the repo:

- `backend/Dockerfile`: local development intended image
- `backend/Dockerfile.production`: intended for production-like environments (production, staging, integration test runs)

To build the local development oriented Docker image by hand, do the following:

```bash
cd backend
docker build . -t your-choice-of-tag -f backend/Dockerfile.production
```

In case you need to build the production oriented image locally, do the following **in the root of the repository** (since the build context requires the `.git` from the repo at build time):

```bash
DOCKER_BUILDKIT=1 docker build . -t your-choice-of-tag -f backend/Dockerfile.production
```

GitHub built images are also made available in the authorisation requiring private registry at `ghcr.io/canonical/test_observer/api` (every main branch commit and tag following the pattern `v*.*.*` gets stored there).
