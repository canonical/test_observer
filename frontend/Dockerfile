FROM ubuntu:22.04 as builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y curl git wget unzip libgconf-2-4 gdb libstdc++6 libglu1-mesa fonts-droid-fallback lib32stdc++6 python3

RUN git clone https://github.com/flutter/flutter.git /opt/flutter && \
    /opt/flutter/bin/flutter doctor && \
    /opt/flutter/bin/flutter channel stable && \
    /opt/flutter/bin/flutter upgrade && \
    /opt/flutter/bin/flutter config --enable-web

ENV PATH $PATH:/opt/flutter/bin

WORKDIR /app
COPY . /app

RUN flutter pub get
RUN flutter pub run build_runner build --delete-conflicting-outputs
RUN flutter build web --release

FROM nginx:stable-alpine

COPY --from=builder /app/build/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]