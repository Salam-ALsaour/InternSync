# InternSync web for the self-hosted server: build the static app, then serve it with Caddy (HTTPS + /api proxy).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Same origin as the API (Caddy proxies /api), so VITE_API_URL stays empty.
RUN npm run build

FROM caddy:2.10-alpine
COPY --from=build /app/dist /srv
