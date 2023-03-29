# Test Observer Backend

## Development Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management.

1. [Install](https://python-poetry.org/docs/#installation) the latest version of Poetry
2. Install dependencies with `poetry install` (No need to create a virtual environment, Poetry does it)
3. Run the server with `uvicorn src.main:app --reload`

## Dependency Management

### Add/Install dependency

`$ poetry add foo`

If it's a dev dependency

`$ poetry add --group dev foo`

### Remove/Uninstall dependency

`$ poetry remove foo`
