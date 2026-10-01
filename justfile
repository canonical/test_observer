# NOTE: Remember to set TEST_OBSERVER_API_URL to a valid URL and set
# TEST_OBSERVER_API_KEY to a read-only key

# Show this help message
default:
    @just --list

# Start the frontend container
up:
    @./scripts/up.sh

# Stop the frontend container
down:
    @./scripts/down.sh

# Install SvelteKit frontend dependencies
sveltekit-install:
    cd frontend/sveltekit && npm ci

# Lint and type check the SvelteKit frontend
sveltekit-lint:
    cd frontend/sveltekit && npm run lint
    cd frontend/sveltekit && npm run check

# Auto-fix SvelteKit frontend formatting and lint issues
sveltekit-lint-fix:
    cd frontend/sveltekit && npm run lint:fix
