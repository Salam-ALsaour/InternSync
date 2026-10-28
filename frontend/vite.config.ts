import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import vercel from "./vercel.json";

// The API is reached through the dev server's proxy, so the browser sees one origin (no CORS in development).
const target = process.env.API_PROXY_TARGET ?? "http://localhost:8000";
// The production preview sends the security headers of the hosted app (vercel.json), so they are tested locally.
const security = Object.fromEntries(vercel.headers[0].headers.map((h) => [h.key, h.value]));

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": { target, changeOrigin: true } } },
  preview: { port: 5173, proxy: { "/api": { target, changeOrigin: true } }, headers: security },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
