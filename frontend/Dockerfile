FROM ubuntu:22.04 as builder

ENV TEST_OBSERVER_API_BASE_URI=http://localhost:30000
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y curl git wget unzip libgconf-2-4 gdb libstdc++6 libglu1-mesa fonts-droid-fallback lib32stdc++6 python3

RUN git clone https://github.com/flutter/flutter.git /opt/flutter && \
    cd /opt/flutter && git checkout '3.7.9' && \
    /opt/flutter/bin/flutter doctor && \
    /opt/flutter/bin/flutter config --enable-web

ENV PATH $PATH:/opt/flutter/bin

WORKDIR /app
COPY . /app

RUN flutter pub get
RUN flutter pub run build_runner build --delete-conflicting-outputs
RUN flutter build web --release

FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y nginx
RUN rm /etc/nginx/sites-enabled/default

COPY --from=builder /app/build/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/sites-available/test-observer-frontend
RUN ln -s /etc/nginx/sites-available/test-observer-frontend /etc/nginx/sites-enabled/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
