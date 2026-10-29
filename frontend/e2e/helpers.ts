/** Shared steps of the browser tests: the demo accounts and signing in through the login page. */
import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const PASSWORD = "Demo-2026-pass";
export const ACCOUNTS = {
  student: "s1@iau.edu.sa",
  company: "sara@nakheel.example",
  academic: "f.alharbi@iau.edu.sa",
  coordinator: "coordinator@iau.edu.sa",
  admin: "admin@internsync.example",
} as const;
export type Who = keyof typeof ACCOUNTS;

export async function signIn(page: Page, who: Who): Promise<void> {
  await page.goto("/login");
  await page.locator("input[type=email]").fill(ACCOUNTS[who]);
  await page.locator("input[type=password]").fill(PASSWORD);
  await page.locator("button[type=submit]").click();
  await expect(page).not.toHaveURL(/\/login/);
  await expect(page.locator("main")).toBeVisible();
}

/** A bearer token for API calls made by the test itself (to find IDs), not by the page. */
export async function token(request: APIRequestContext, who: Who): Promise<string> {
  const r = await request.post("/api/v1/auth/login", { data: { email: ACCOUNTS[who], password: PASSWORD } });
  expect(r.ok()).toBeTruthy();
  return (await r.json()).access_token as string;
}

export async function apiGet<T>(request: APIRequestContext, path: string, bearer: string): Promise<T> {
  const r = await request.get(`/api/v1${path}`, { headers: { Authorization: `Bearer ${bearer}` } });
  expect(r.ok(), await r.text()).toBeTruthy();
  return (await r.json()) as T;
}

/** NFR-USA-03: the page is no wider than the window. */
export async function noSideScroll(page: Page): Promise<void> {
  const [scroll, width] = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  expect(scroll, "horizontal scrolling").toBeLessThanOrEqual(width + 1);
}
