# ---- Build stage ----
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- Serve stage ----
FROM nginx:1.27-alpine

# Static assets
COPY --from=build /app/dist /usr/share/nginx/html

# nginx config template — envsubst fills ${PORT} at container start (via the
# official image's /etc/nginx/templates mechanism). $uri etc. are NOT env vars
# so they are left untouched.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Runtime config script: writes window.__BACKEND_URL__ into config.js from the
# BACKEND_URL env var before nginx starts.
COPY docker-config.sh /docker-entrypoint.d/40-write-config.sh
RUN chmod +x /docker-entrypoint.d/40-write-config.sh

# Default port (Render overrides via $PORT; docker-compose maps to it).
ENV PORT=80
EXPOSE 80
