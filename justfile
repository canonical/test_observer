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
