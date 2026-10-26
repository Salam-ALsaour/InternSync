/** FR-LOC-02: Arabic and English have the same keys, and every key the code uses exists in both. */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import ar from "./ar.json";
import en from "./en.json";

type Tree = { [k: string]: string | Tree };

function flatten(tree: Tree, prefix = ""): Map<string, string> {
  const out = new Map<string, string>();
  for (const [k, v] of Object.entries(tree)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (typeof v === "string") out.set(key, v);
    else for (const [kk, vv] of flatten(v, key)) out.set(kk, vv);
  }
  return out;
}

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return sources(path);
    return /\.tsx?$/.test(name) && !name.endsWith(".test.ts") ? [path] : [];
  });
}

const AR = flatten(ar as Tree);
const EN = flatten(en as Tree);

describe("translation keys", () => {
  it("Arabic and English have exactly the same keys", () => {
    expect([...AR.keys()].filter((k) => !EN.has(k))).toEqual([]);
    expect([...EN.keys()].filter((k) => !AR.has(k))).toEqual([]);
  });

  it("no translation is empty", () => {
    expect([...AR].filter(([, v]) => !v.trim()).map(([k]) => k)).toEqual([]);
    expect([...EN].filter(([, v]) => !v.trim()).map(([k]) => k)).toEqual([]);
  });

  it("every literal key used in the code exists", () => {
    const used = new Set<string>();
    for (const file of sources(join(__dirname, ".."))) {
      const text = readFileSync(file, "utf8");
      for (const m of text.matchAll(/\bt\(\s*"([a-z_]+\.[a-z0-9_.]+)"/g)) used.add(m[1]);
    }
    expect(used.size).toBeGreaterThan(200);
    expect([...used].filter((k) => !AR.has(k)).sort()).toEqual([]);
  });

  it("the placeholders match in both languages", () => {
    const vars = (s: string) => [...s.matchAll(/\{\{(\w+)\}\}/g)].map((m) => m[1]).sort().join(",");
    expect([...AR].filter(([k, v]) => vars(v) !== vars(EN.get(k) ?? "")).map(([k]) => k)).toEqual([]);
  });
});
