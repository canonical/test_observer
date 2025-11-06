FROM node:20-alpine AS builder

# Install dependencies and build CSS
WORKDIR /build
COPY package*.json ./
RUN npm ci --only=production
COPY sass ./sass
RUN npm run build

# Production image
FROM nginx:alpine

# Copy built CSS and static files
COPY --from=builder /build/css /usr/share/nginx/html/css
COPY index.html /usr/share/nginx/html/
COPY js /usr/share/nginx/html/js
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
