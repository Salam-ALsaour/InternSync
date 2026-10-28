import { readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const pub = (path: string) => resolve(__dirname, "../public", path);
const manifest = JSON.parse(readFileSync(pub("manifest.webmanifest"), "utf8"));
const worker = readFileSync(pub("sw.js"), "utf8");

describe("installable app (AT-PWA-01, FR-PWA-03)", () => {
  it("has the manifest fields browsers need to install it", () => {
    expect(manifest.name).toBeTruthy();
    expect(manifest.short_name).toBe("InternSync");
    expect(manifest.start_url).toBe("/");
    expect(manifest.display).toBe("standalone");
    expect(manifest.theme_color).toMatch(/^#[0-9A-F]{6}$/i);
    const sizes = manifest.icons.map((i: { sizes: string }) => i.sizes);
    expect(sizes).toEqual(expect.arrayContaining(["192x192", "512x512"]));
    expect(manifest.icons.some((i: { purpose: string }) => i.purpose === "maskable")).toBe(true);
    for (const icon of manifest.icons) expect(statSync(pub(icon.src.slice(1))).size).toBeGreaterThan(500);
  });

  it("caches the app shell but never an API answer", () => {
    expect(worker).toContain('"/index.html"');
    expect(worker).toContain('url.pathname.startsWith("/api/")) return');
    expect(worker).toContain('request.method !== "GET"');
  });

  it("is linked from the page", () => {
    const html = readFileSync(resolve(__dirname, "../index.html"), "utf8");
    expect(html).toContain('rel="manifest" href="/manifest.webmanifest"');
    expect(html).toContain("apple-touch-icon");
  });
});
