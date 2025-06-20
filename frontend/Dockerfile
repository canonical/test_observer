FROM ubuntu:24.04 as builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y curl git wget unzip gdb libstdc++6 libglu1-mesa fonts-droid-fallback python3

RUN git clone https://github.com/flutter/flutter.git /opt/flutter && \
    cd /opt/flutter && git checkout '3.32.4' && \
    /opt/flutter/bin/flutter doctor && \
    /opt/flutter/bin/flutter config --enable-web

ENV PATH $PATH:/opt/flutter/bin

WORKDIR /app
COPY . /app

RUN flutter pub get
RUN flutter pub run build_runner build --delete-conflicting-outputs
RUN flutter build web --release
# Cache busting so that users don't have to hard refresh
RUN RANDOMVALUE=`tr -dc A-Za-z0-9 </dev/urandom | head -c 13` && \
    mv build/web/flutter_bootstrap.js build/web/flutter_bootstrap.$RANDOMVALUE.js && \
    mv build/web/main.dart.js build/web/main.dart.$RANDOMVALUE.js && \
    find build/web/ -type f -exec sed -i -e 's/flutter_bootstrap.js/flutter_bootstrap.'$RANDOMVALUE'.js/g' {} \; && \
    find build/web/ -type f -exec sed -i -e 's/main.dart.js/main.dart.'$RANDOMVALUE'.js/g' {} \;

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y nginx
RUN rm /etc/nginx/sites-enabled/default

COPY --from=builder /app/build/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/sites-available/test-observer-frontend
RUN ln -s /etc/nginx/sites-available/test-observer-frontend /etc/nginx/sites-enabled/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
