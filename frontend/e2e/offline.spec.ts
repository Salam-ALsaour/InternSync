/** AT-PWA-03 as changed by CR-10: offline, a page opened before shows its saved copy, a page never opened says so,
 *  a report draft typed offline is saved when the connection returns, and nothing is left after sign-out. */
import { expect, test } from "@playwright/test";
import { apiGet, navTo, openMenu, signIn, token } from "./helpers";

test("offline: saved copy, not-saved notice, draft saved on reconnect, nothing left after sign-out",
  async ({ page, context, request }) => {
    await signIn(page, "student");
    const bearer = await token(request, "student");
    const placements = await apiGet<{ items: { id: string; status: string }[] }>(request, "/placements", bearer);
    const active = placements.items.find((p) => p.status === "active")!;
    const slots = await apiGet<{ id: string; status: string; kind: string; week_no: number | null }[]>(
      request, `/placements/${active.id}/report-slots`, bearer);
    const open = slots.filter((s) => s.kind === "weekly" && s.status === "draft").at(-1)!;

    await navTo(page, "/student/reports");
    await expect(page.locator("main table").first()).toBeVisible();
    await page.goto(`/reports/${open.id}`);  // a full reload: the saved copy of the session comes back
    await expect(page.locator("textarea").first()).toBeVisible();

    await context.setOffline(true);
    await navTo(page, "/student/reports");
    await expect(page.locator("main table").first()).toBeVisible();
    await expect(page.getByRole("status")).toContainText(/نسخة محفوظة|Saved copy/);
    await navTo(page, "/student/profile");
    await expect(page.getByRole("status")).toContainText(/غير محفوظ على هذا الجهاز|not saved on this device/);

    await page.goBack();
    await page.goBack();
    await expect(page).toHaveURL(new RegExp(`/reports/${open.id}`));
    const text = `Written offline ${test.info().project.name} ${Date.now()}`;
    await page.locator("textarea").nth(1).fill(text);
    await expect(page.getByText(/نصّك محفوظ على هذا الجهاز|kept on this device/)).toBeVisible();
    await expect(page.getByRole("button", { name: /حفظ المسودة|Save draft/ })).toBeDisabled();

    await context.setOffline(false);
    await expect(page.getByText(/نصّك محفوظ على هذا الجهاز|kept on this device/)).toBeHidden({ timeout: 15_000 });
    await expect.poll(async () => (await apiGet<{ draft: { learning: string | null } | null }>(
      request, `/report-slots/${open.id}`, bearer)).draft?.learning).toBe(text);

    await openMenu(page);
    await page.getByRole("button", { name: /تسجيل الخروج|Log out|Sign out/ }).click();
    await expect(page).toHaveURL(/\/login/);
    const left = await page.evaluate(() => ({
      saved: sessionStorage.getItem("internsync.saved"),
      drafts: Object.keys(localStorage).filter((k) => k.startsWith("internsync.draft.")),
    }));
    expect(left).toEqual({ saved: null, drafts: [] });
  });
