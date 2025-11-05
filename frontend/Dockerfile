FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./

# Install dependencies
RUN npm install

COPY . .

# Build the application  
RUN npm run build

FROM nginx:alpine
RUN rm /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/test-observer-frontend.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
