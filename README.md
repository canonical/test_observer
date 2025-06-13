# Test Observer

Test Observer (TO) is a dashboard for viewing the results of tests run on different environments for a particular artefact. A user interested in testing an artefact (a deb, snap, charm or image) under different environments (particular machines or cloud setups) can use TO as means for storing, viewing and comparing results with previous runs or versions of an artefact. The last use case is particularly useful for catching regressions. Additionally, TO provides a mechanism to assign reviewers that can look at results and mark artefacts as approved or failed to gate updates. It is important to note that TO does not run the tests itself, but provides an API with which users can report the results to.

Certification currently deploys an instance of TO that they used for reviewing Stable Release Updates (SRUs). Other teams also use this instance for their tests. You can visit the [frontend](https://test-observer.canonical.com/) and view the [API docs](https://test-observer-api.canonical.com/docs), although this currently requires Canonical VPN access. There's also a staging deployment of [frontend](https://test-observer-staging.canonical.com/) and [API](https://test-observer-api-staging.canonical.com/docs) that teams can use to test their integration.

## Run locally

### Docker Compose (Recommended for Development)

The easiest way to run the full Test Observer stack locally is using Docker Compose:

```bash
# Start the complete stack (backend, frontend, database)
# Migrations and test data seeding happen automatically
docker-compose up

# Start without test data seeding
SEED_DATA=false docker-compose up

# Run in detached mode
docker-compose up -d

# Stop the stack
docker-compose down

# Rebuild containers after code changes
docker-compose up --build
```

This will start:
- **Backend API** at `http://localhost:30000` (with automatic migrations and seeding)
- **Frontend** at `http://localhost:8080`
- **PostgreSQL database** with persistent storage

### Individual Components

For component-specific development, see the [backend](/backend/README.md) and [frontend](/frontend/README.md) documentation.

### Production-like Environment

To run the whole system via Terraform, juju and charms simulating production and staging environments, use [terraform](/terraform/README.md)


## Charm integration tests

A charmed Test Observer deployment can be integration tested using `charmcraft test` (which itself internally uses a classically confined copy of [spread](https://github.com/canonical/spread) bundled with `charmcraft`).

The integration tests are runnable either locally (using [lxd](https://documentation.ubuntu.com/lxd/en/latest/installing/) at the time of writing) or using GitHub. Alternative test execution backends are configurable by adding new `adhoc` backends next to `lxd` and `github` in the [spread.yaml](./spread.yaml).

### Run integration tests locally

Tests can be run locally with either `charmcraft test lxd` or `charmcraft.spread lxd` (the latter gives a bit more verbose log output).

```bash
charmcraft.spread -v lxd
```

### Jump into a `spread` provided shell environment

To debug the charm integration tests, you can jump into a `spread` provided environment for the test execution either before, instead of the test task, or after a test task has been executed (you could also combine this choosing to run only a specific test scenario).

```bash
# open a shell to the execution environment _before_ executing each test task 
charmcraft.spread -v -shell lxd 

# open a shell to the execution environment _instead of_ executing each test task 
charmcraft.spread -v -shell lxd

# open a shell to the execution environment _after_ of executing each test task 
charmcraft.spread -v -shell-after lxd
```