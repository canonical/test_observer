FROM ubuntu:24.04 as builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y \
    curl git wget unzip gdb libstdc++6 libglu1-mesa fonts-droid-fallback \
    python3 npm

RUN git clone https://github.com/flutter/flutter.git /opt/flutter && \
    cd /opt/flutter && git checkout '3.29.3' && \
    /opt/flutter/bin/flutter doctor && \
    /opt/flutter/bin/flutter config --enable-web

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

WORKDIR /vue-app
COPY ./vue_poc/package*.json ./
RUN npm install

COPY ./vue_poc/ ./
RUN npm run build

WORKDIR /react-app
COPY ./react_poc/package*.json ./
RUN npm install

COPY ./react_poc/ ./
RUN npm run build

WORKDIR /svelte-app
COPY ./svelte_poc/package*.json ./
RUN npm install

COPY ./svelte_poc/ ./
RUN npm run build

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y nginx
RUN rm /etc/nginx/sites-enabled/default

COPY --from=builder /app/build/web /usr/share/nginx/html
COPY --from=builder /vue-app/dist /usr/share/nginx/html/vue_poc
COPY --from=builder /react-app/dist /usr/share/nginx/html/react_poc
COPY --from=builder /svelte-app/dist /usr/share/nginx/html/svelte_poc
COPY nginx.conf /etc/nginx/sites-available/test-observer-frontend
RUN ln -s /etc/nginx/sites-available/test-observer-frontend /etc/nginx/sites-enabled/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
