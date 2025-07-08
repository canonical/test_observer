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

RUN apt-get update && \
    apt-get install -y python3.12 curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/home/app

COPY uv.lock .
COPY pyproject.toml .
COPY . .

ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --all-groups

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s CMD curl --fail http://localhost:30000/v1/version || exit 1

WORKDIR /home/app

CMD ["./dev_entrypoint.sh"]
