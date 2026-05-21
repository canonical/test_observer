# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

FROM ubuntu:24.04 as builder

ENV DEBIAN_FRONTEND=noninteractive
# Prevent tar from attempting chown to UIDs outside the LXD user namespace.
ENV TAR_OPTIONS="--no-same-owner"
RUN apt-get update && \
    apt-get install -y \
    curl git wget unzip gdb libstdc++6 libglu1-mesa fonts-droid-fallback \
    python3

RUN git clone --depth 1 --branch 3.29.3 https://github.com/flutter/flutter.git /opt/flutter && \
    cd /opt/flutter && \
    /opt/flutter/bin/flutter config --enable-web --no-enable-android

ENV PATH $PATH:/opt/flutter/bin

WORKDIR /app

# Disabling full copy of the immediate directory.  Before the Flutter build, let's *just* copy the files needed for Flutter.
# This will minimize rebuilding of much of the Flutter code unless there is a true need for it.
#COPY . /app
COPY lib /app/lib
COPY assets /app/assets
COPY benchmarks /app/benchmarks
COPY integration_test /app/integration_test
COPY test /app/test
COPY test_driver /app/test_driver
COPY web /app/web
COPY .vscode /app/.vscode
COPY analysis_options.yaml frontend.iml LICENSE .metadata pubspec.* run_benchmark_tests.dart run_integration_tests.sh /app/

# NOTE: Skipping charm directory, as well as Docker and Git-related files

RUN flutter pub get
RUN flutter pub run build_runner build --delete-conflicting-outputs
RUN flutter build web --release

# Cache busting so that users don't have to hard refresh
RUN RANDOMVALUE=`tr -dc A-Za-z0-9 </dev/urandom | head -c 13` && \
    mv build/web/flutter_bootstrap.js build/web/flutter_bootstrap.$RANDOMVALUE.js && \
    mv build/web/main.dart.js build/web/main.dart.$RANDOMVALUE.js && \
    find build/web/ -type f -exec sed -i -e 's/flutter_bootstrap.js/flutter_bootstrap.'$RANDOMVALUE'.js/g' {} \; && \
    find build/web/ -type f -exec sed -i -e 's/main.dart.js/main.dart.'$RANDOMVALUE'.js/g' {} \;

# ---------------------------------------------------------------------------
# SvelteKit WIP frontend (served at /wip)
# To change the web root, update BASE_PATH here. It is the single source of
# truth — svelte.config.js reads it via process.env.BASE_PATH at build time.
# ---------------------------------------------------------------------------
FROM node:20-alpine AS sveltekit-builder

ENV TAR_OPTIONS="--no-same-owner"

ARG APT_PROXY
RUN if [ -n "$APT_PROXY" ]; then npm config set proxy "$APT_PROXY"; fi

WORKDIR /app/sveltekit
COPY sveltekit/package.json ./
COPY sveltekit/vendor ./vendor
RUN npm install
COPY sveltekit .
ENV BASE_PATH=/wip
RUN npm run build

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y nginx
RUN rm /etc/nginx/sites-enabled/default

COPY --from=builder /app/build/web /usr/share/nginx/html
COPY --from=sveltekit-builder /app/sveltekit/build /usr/share/nginx/html/wip
COPY nginx.conf /etc/nginx/sites-available/test-observer-frontend
RUN ln -s /etc/nginx/sites-available/test-observer-frontend /etc/nginx/sites-enabled/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
