# InternSync web (Increment 1 design, Section 9). Local demo: Vite serves the app and proxies /api to the API.
FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
