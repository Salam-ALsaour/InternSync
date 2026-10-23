/// <reference types="vitest" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The API is reached through the dev server's proxy, so the browser sees one origin (no CORS in development).
const target = process.env.API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": { target, changeOrigin: true } } },
  preview: { port: 5173, proxy: { "/api": { target, changeOrigin: true } } },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
