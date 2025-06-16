FROM ubuntu:24.04

ARG UV_DYNAMIC_VERSIONING_BYPASS=0.0.0

COPY --from=ghcr.io/astral-sh/uv:0.6.5 /uv /uvx /bin/
ENV UV_SYSTEM_PYTHON=true
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV VIRTUAL_ENV=/home/app/.venv
ENV PATH=/home/app/.venv/bin:$PATH

EXPOSE 30000

WORKDIR /home/app

RUN echo "Version: ${VERSION}"

RUN apt-get update && \
    apt-get install -y python3.12 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/home/app

# Issue tracking API credentials (optional - can be set at runtime)
ENV GITHUB_TOKEN=""
ENV JIRA_USERNAME=""
ENV JIRA_TOKEN=""
ENV JIRA_BASE_URL="https://warthogs.atlassian.net"

COPY uv.lock .
COPY pyproject.toml .
COPY . .

# Make scripts executable
RUN chmod +x entrypoint.sh wait_for_db.py wait_for_app.py

ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --group test

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl --fail http://localhost:30000/v1/version || exit 1

WORKDIR /home/app

CMD ["./entrypoint.sh"]
