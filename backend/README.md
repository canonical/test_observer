# Test Observer Backend

## Development Setup

The development setup is prepared through the docker compose found in the parent directory. The dependencies are managed through uv. The migrations through alembic. Tests are run using PyTest. And finally we use pre-commit to maintain the OpenAPI schema.

## Starting and stopping the backend

To start the back-end, run the following command in the project's root directory:
```bash
docker compose up --build test-observer-api
```

Then to stop it, first press Ctrl+C. Then run the following command:
```bash
docker compose down --volumes
```

Note: the backend has CORS middleware that allows for connections from localhost:30001. That means in order for a locally deployed frontend to connect to a locally deployed backend, the frontend needs to run on port 30001 and on the same host.

## Managing dependencies

Dependencies are managed through uv. To install them locally you can run the following:
```bash
uv sync --all-groups
```
Note: that if you run docker compose up after installing the dependencies locally, the docker container will overwrite the locally installed dependencies. The issue is that the docker container doesn't install all dependency groups, so you will be missing some dependencies (for instance pytest wont be there). If that happens you can just install the dependencies locally again using the command above.

You can add dependencies using:
```bash
uv add <dependency>
```
Note: if you are adding a test dependency make sure to pass `--group test`, and if it's a dev dependency pass `--group dev`.

## Set up pre-commit

The project uses [pre-commit](https://pre-commit.com) to auto generate OpenAPI schema file. To set it up for your working copy of the repository:

```bash
sudo apt install pre-commit jq
pre-commit install # in the `backend` directory
```

## Database Migrations

The project uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) to manage database migrations. Migrations will be applied automatically when running the project through docker compose. But making changes to data models requires manually creating and applying migrations.

### Create Migrations

For more information on how to create migrations, please check [Alembic docs](https://alembic.sqlalchemy.org/en/latest/). Note, that it's worth noting that Alembic can help [auto generate migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) based on differences between SQLAlchemy ORMs and the actual database. But developers have to check these migrations to make sure they're fine. To generate migrations automatically though, just run:

```bash
docker compose exec test-observer-api alembic revision --autogenerate -m "Migration description"
```

Note: the created migration file will be owned by root therefore you wont be able to edit it as is. To fix this, you can just run the following commands:

```bash
sudo chown youruser:youruser migrations/versions/migration-file.py
chmod g+w migrations/versions/migration-file.py
```

Note: do not assume the automatically generated migrations are correct. More often than not you have to make changes to make sure it does exactly what you need. For instance, if you're adding a new not nullable column to a table, then you must provide some sort of server default. Alembic doesn't do this for you.

### Applying Migrations

Since the database is in microk8s cluster, migrations have to be applied inside the cluster and not on the host machine. To do that we can just run the migrations on our api service which will run in one of the api pods through:

```bash
docker compose exec test-observer-api alembic upgrade head
```

You can also roll back migrations using:
```bash
docker compose exec test-observer-api alembic downgrade -1
```

## Tests

Testing is handled using pytest package and can be run using the command:
```bash
docker compose exec test-observer-api pytest
```

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
