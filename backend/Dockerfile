# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

FROM ubuntu:24.04

ARG UV_DYNAMIC_VERSIONING_BYPASS=0.0.0

COPY --from=ghcr.io/astral-sh/uv:0.6.5 /uv /uvx /bin/
ENV UV_SYSTEM_PYTHON=true
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV VIRTUAL_ENV=/home/app/.venv
ENV PATH=/home/app/.venv/bin:$PATH

EXPOSE 30000
EXPOSE 9090

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
