/** AT-CER-02 in the browser: the public check without login; valid and altered codes. */
import { expect, test } from "@playwright/test";
import { apiGet, token } from "./helpers";

test("certificate check: valid, altered, and typed with dashes", async ({ page, request }) => {
  const bearer = await token(request, "coordinator");
  const [cert] = await apiGet<{ code: string }[]>(request, "/certificates?status=valid", bearer);
  await page.goto(`/verify/${cert.code}`);
  await expect(page.getByRole("status")).toContainText(/شهادة سارية|Valid certificate/);
  await expect(page.locator("main, body")).toContainText(/لمى الحربي|Lama Al-Harbi/);
  await expect(page.locator("body")).not.toContainText(/الدرجة النهائية|Total/);

  const altered = (cert.code[0] === "B" ? "C" : "B") + cert.code.slice(1);
  await page.goto(`/verify/${altered}`);
  await expect(page.getByRole("status")).toContainText(/لا توجد شهادة بهذا الرمز|No certificate has this code/);

  await page.goto("/verify");
  const grouped = cert.code.match(/.{1,4}/g)!.join("-").toLowerCase();
  await page.locator("input").fill(grouped);
  await page.locator("button[type=submit]").click();
  await expect(page.getByRole("status")).toContainText(/شهادة سارية|Valid certificate/);
});
