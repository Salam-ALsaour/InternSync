/** NFR-PRT-01: the main task of each role, on every browser project; NFR-USA-03 at each project's size. */
import { expect, test } from "@playwright/test";
import { apiGet, noSideScroll, signIn, token } from "./helpers";

test("student: dashboard, reports, and a draft saved", async ({ page, request }) => {
  await signIn(page, "student");
  await expect(page).toHaveURL(/\/student$/);
  await noSideScroll(page);
  const bearer = await token(request, "student");
  const placements = await apiGet<{ items: { id: string; status: string }[] }>(request, "/placements", bearer);
  const active = placements.items.find((p) => p.status === "active")!;
  const slots = await apiGet<{ id: string; status: string; kind: string }[]>(
    request, `/placements/${active.id}/report-slots`, bearer);
  const open = slots.find((s) => s.kind === "weekly" && s.status === "draft")!;
  await page.goto(`/reports/${open.id}`);
  const box = page.locator("textarea").first();
  await box.fill(`Browser test ${test.info().project.name} ${Date.now()}`);
  await page.getByRole("button", { name: /حفظ المسودة|Save draft/ }).click();
  await expect(page.getByText(/تم حفظ المسودة|Draft saved/).first()).toBeVisible();
  await noSideScroll(page);
});

test("company supervisor: trainees and attendance", async ({ page }) => {
  await signIn(page, "company");
  await page.goto("/company/trainees");
  await expect(page.locator("main table, main ul").first()).toBeVisible();
  await page.locator("main a").filter({ hasText: /فتح|Open/ }).first().click();
  await expect(page).toHaveURL(/\/placements\//);
  await noSideScroll(page);
});

test("academic supervisor: students and the similarity list", async ({ page }) => {
  await signIn(page, "academic");
  await page.goto("/academic/students");
  await expect(page.locator("main")).toContainText(/عبدالله الشهري|Abdullah/);
  await page.goto("/academic/similarity");
  await expect(page.locator("main h1")).toBeVisible();
  await noSideScroll(page);
});

test("coordinator: cycle statistics with the leniency alert, and certificates", async ({ page }) => {
  await signIn(page, "coordinator");
  await page.goto("/coordinator/cycles");
  await page.locator("tr", { hasText: "Summer 2025 (demo)" }).getByRole("link").click();
  await page.getByRole("tab", { name: /الإحصاءات|Statistics/ }).click();
  await expect(page.getByText(/أعلى بكثير من متوسط الدورة|Well above the cycle mean/)).toBeVisible();
  await page.goto("/coordinator/certificates");
  await expect(page.locator("main")).toContainText(/لمى الحربي|Lama Al-Harbi/);
  await noSideScroll(page);
});

test("platform admin: organizations, in both languages", async ({ page }) => {
  await signIn(page, "admin");
  await page.goto("/platform/organizations");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await page.getByRole("button", { name: /English|العربية/ }).click();
  await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
  await expect(page.locator("main h1")).toBeVisible();
  await page.getByRole("button", { name: /العربية|English/ }).click();
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
});
