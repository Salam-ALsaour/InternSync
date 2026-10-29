/** Takes the screenshots of docs/User_Guide.md from the demo data, in English (Increment 5, RQ-5). Run with
 *  `npx playwright test -c playwright.guide.config.ts` on a database with fresh demo data: it submits a report. */
import { type APIRequestContext, devices, expect, type Page, test } from "@playwright/test";
import { ACCOUNTS, apiGet, navTo, PASSWORD, type Who } from "./helpers";

const OUT = "../docs/User_Guide";
const FORMER = "s10@iau.edu.sa";
// The opening of the former student's accepted report (seed data): copying it shows a similarity flag.
const COPIED = "This week I worked on the order service of the e-commerce platform. I wrote a new endpoint that " +
  "returns the order history of a customer with pagination and filters by date and status. To make the query fast " +
  "I added a composite index on the customer and created date columns, which reduced the response time from two " +
  "seconds to about two hundred milliseconds.";

async function bearer(request: APIRequestContext, email: string): Promise<string> {
  const r = await request.post("/api/v1/auth/login", { data: { email, password: PASSWORD } });
  expect(r.ok(), await r.text()).toBeTruthy();
  const token = (await r.json()).access_token as string;
  await request.patch("/api/v1/me", { headers: { Authorization: `Bearer ${token}` }, data: { language: "en" } });
  return token;
}

async function signIn(page: Page, email: string): Promise<void> {
  await page.goto("/login");
  await page.evaluate(() => sessionStorage.clear());
  await page.goto("/login");
  await page.locator("input[type=email]").fill(email);
  await page.locator("input[type=password]").fill(PASSWORD);
  await page.locator("button[type=submit]").click();
  await expect(page).not.toHaveURL(/\/login/);
  await expect(page.locator("main h1").first()).toBeVisible();
}

/** A screenshot of the window once `wait` shows; with `top`, the page is first scrolled so that text is at the top. */
async function shot(page: Page, name: string, wait?: string | RegExp, top?: string | RegExp): Promise<void> {
  if (wait) await expect(page.getByText(wait).first()).toBeVisible({ timeout: 60_000 });
  await page.waitForLoadState("networkidle");
  if (top) await page.getByText(top).first().evaluate((el) => el.scrollIntoView({ block: "start" }));
  await page.screenshot({ path: `${OUT}/${name}.png` });
}

test("user guide screenshots", async ({ page, request, browser }) => {
  const token = Object.fromEntries(await Promise.all((Object.keys(ACCOUNTS) as Who[])
    .map(async (who) => [who, await bearer(request, ACCOUNTS[who])])));
  await bearer(request, FORMER);
  const student = token.student;
  const placement = (await apiGet<{ items: { id: string; status: string }[] }>(request, "/placements", student))
    .items.find((p) => p.status === "active")!;
  const slots = await apiGet<{ id: string; status: string; kind: string; week_no: number | null }[]>(
    request, `/placements/${placement.id}/report-slots`, student);
  const drafts = slots.filter((s) => s.kind === "weekly" && s.status === "draft");
  const [copiedSlot, writingSlot] = [drafts[0], drafts[1]];
  const auth = { Authorization: `Bearer ${student}` };
  await request.put(`/api/v1/report-slots/${copiedSlot.id}/draft`, { headers: auth, data: {
    tasks_performed: COPIED, learning: "Indexes matter more than caching for this query.",
    challenges: "Reading the slow query log.", next_week_plan: "Add tests for the filters." } });
  await request.post(`/api/v1/report-slots/${copiedSlot.id}/submit`, { headers: auth });
  await request.put(`/api/v1/report-slots/${writingSlot.id}/draft`, { headers: auth, data: {
    tasks_performed: "Built the export of the monthly sales report to Excel and reviewed two pull requests.",
    learning: "How to stream a large file instead of building it in memory.", challenges: "",
    next_week_plan: "" } });

  // Getting started
  await page.goto("/login");
  await page.getByRole("button", { name: "English" }).click();
  await shot(page, "01-sign-in", "Log in");

  // Student
  await signIn(page, ACCOUNTS.student);
  await shot(page, "02-student-home");
  await page.goto("/student/vacancies");
  await shot(page, "03-student-recommended", /Advisory/i);
  await page.goto(`/reports/${writingSlot.id}`);
  await shot(page, "04-student-report", /Save draft/);
  await signIn(page, FORMER);
  await page.goto("/student/feedback");
  await shot(page, "05-student-feedback", /Evaluation of the training company/);

  // Company supervisor (the Company Admin of the demo company)
  await signIn(page, ACCOUNTS.company);
  await page.goto("/company/trainees");
  await shot(page, "06-company-trainees");
  await page.goto(`/placements/${placement.id}?tab=attendance`);
  await shot(page, "07-company-attendance");
  await page.goto(`/placements/${placement.id}?tab=evaluations`);
  await shot(page, "08-company-evaluation");

  // Academic supervisor: the copied report with its similarity flag
  const version = (await apiGet<{ submitted: { id: string }[] }>(request, `/report-slots/${copiedSlot.id}`,
    token.academic)).submitted[0].id;
  await expect.poll(async () => (await apiGet<{ status: string }>(request,
    `/report-versions/${version}/similarity`, token.academic)).status, { timeout: 120_000 }).toBe("done");
  await signIn(page, ACCOUNTS.academic);
  await page.goto(`/reports/${copiedSlot.id}`);
  await shot(page, "09-academic-similarity", /Advisory/i);

  // Coordinator
  await signIn(page, ACCOUNTS.coordinator);
  await shot(page, "10-coordinator-home");
  const cycles = await apiGet<{ id: string; name: string }[]>(request, "/cycles", token.coordinator);
  const summer = cycles.find((c) => c.name === "Summer 2025 (demo)")!;
  await page.goto(`/coordinator/cycles/${summer.id}`);
  await page.getByRole("tab", { name: "Statistics" }).click();
  await shot(page, "11-coordinator-cycle-statistics", /Well above the cycle mean/, "Final evaluations by company");
  const [cert] = await apiGet<{ code: string; placement_id: string }[]>(request, "/certificates?status=valid",
    token.coordinator);
  await page.goto(`/placements/${cert.placement_id}?tab=grade`);
  await shot(page, "12-coordinator-certificate", /Completion certificate/, "Completion certificate");
  await page.goto("/coordinator/exports");
  await shot(page, "13-coordinator-exports");

  // Platform Admin
  await signIn(page, ACCOUNTS.admin);
  await shot(page, "14-platform-admin-home");

  // Phone: the public certificate check and the offline notice
  const phone = await browser.newContext({ ...devices["iPhone 14"], baseURL: test.info().project.use.baseURL });
  const mobile = await phone.newPage();
  await mobile.goto("/login");
  await mobile.getByRole("button", { name: "English" }).click();
  await mobile.goto(`/verify/${cert.code}`);
  await shot(mobile, "15-phone-certificate-check", /Valid certificate/);
  await signIn(mobile, ACCOUNTS.student);
  await navTo(mobile, "/student/reports");
  await expect(mobile.locator("main table").first()).toBeVisible();
  await phone.setOffline(true);
  await navTo(mobile, "/student");
  await shot(mobile, "16-phone-offline", /Saved copy/, /You are offline/);
  await phone.close();
});
