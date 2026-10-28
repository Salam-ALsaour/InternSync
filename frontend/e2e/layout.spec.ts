/** NFR-USA-03 (360 to 1920 px without horizontal scrolling) and NFR-USA-04 (contrast, automated with axe). The
 *  layout does not depend on the engine, so these run once, on Chromium. */
import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";
import { ACCOUNTS, noSideScroll, PASSWORD, signIn, type Who } from "./helpers";

const PAGES: [Who, string[]][] = [
  ["student", ["/student", "/student/reports", "/student/vacancies", "/student/feedback", "/notifications"]],
  ["coordinator", ["/coordinator", "/coordinator/cycles", "/coordinator/placements", "/coordinator/certificates",
    "/coordinator/exports"]],
];

test.beforeEach(() => {
  test.skip(test.info().project.name !== "chromium", "engine-independent; checked once");
});

for (const width of [360, 768, 1366, 1920]) {
  test(`no horizontal scrolling at ${width} px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/login");
    await noSideScroll(page);
    for (const [who, paths] of PAGES) {
      await signIn(page, who);
      for (const path of paths) {
        await page.goto(path);
        await expect(page.locator("main h1").first()).toBeVisible();
        await noSideScroll(page);
      }
      await page.evaluate(() => sessionStorage.clear());
    }
  });
}

/** Press Tab until the focused element matches, as a keyboard user would. */
async function tabTo(page: Page, matches: (el: Element) => boolean, max = 60): Promise<void> {
  for (let i = 0; i < max; i++) {
    await page.keyboard.press("Tab");
    if (await page.evaluate(`(${matches.toString()})(document.activeElement)`)) return;
  }
  throw new Error("focus never reached the element");
}

test("keyboard only: sign in, open the reports, and save a draft", async ({ page }) => {
  await page.goto("/login");
  await tabTo(page, (el) => el instanceof HTMLInputElement && el.type === "email");
  await page.keyboard.type(ACCOUNTS.student);
  await tabTo(page, (el) => el instanceof HTMLInputElement && el.type === "password");
  await page.keyboard.type(PASSWORD);
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/student$/);
  await tabTo(page, (el) => el.getAttribute("href") === "/student/reports");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/student\/reports/);
  await expect(page.locator("main table").first()).toBeVisible();
  await tabTo(page, (el) => (el.getAttribute("href") ?? "").startsWith("/reports/") &&
    !!el.closest("tr")?.textContent?.match(/مسودة|Draft/));
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/reports\//);
  await tabTo(page, (el) => el instanceof HTMLTextAreaElement);
  await page.keyboard.type(" (keyboard)");
  await tabTo(page, (el) => el instanceof HTMLButtonElement && /حفظ المسودة|Save draft/.test(el.textContent ?? ""));
  await page.keyboard.press("Enter");
  await expect(page.getByText(/تم حفظ المسودة|Draft saved/).first()).toBeVisible();
});

test("text contrast of at least 4.5:1 on the main pages", async ({ page }) => {
  const check = async () => {
    const result = await new AxeBuilder({ page }).withRules(["color-contrast"]).analyze();
    expect(result.violations.flatMap((v) => v.nodes.map((n) => `${page.url()} ${n.target.join(" ")}: ${n.failureSummary}`)))
      .toEqual([]);
  };
  await page.goto("/login");
  await check();
  await page.goto("/verify");
  await check();
  for (const [who, paths] of PAGES) {
    await signIn(page, who);
    for (const path of paths) {
      await page.goto(path);
      await expect(page.locator("main h1").first()).toBeVisible();
      await check();
    }
    await page.evaluate(() => sessionStorage.clear());
  }
});
