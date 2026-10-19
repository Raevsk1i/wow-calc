import { expect, test } from "@playwright/test";
import path from "node:path";

const outDir = "/opt/cursor/artifacts/screenshots";

test("capture simulator demo", async ({ page }) => {
  test.setTimeout(180_000);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "WoW DPS Lab" })).toBeVisible();
  await page.screenshot({ path: path.join(outDir, "01-landing.png"), fullPage: true });

  await page.locator("select").nth(0).selectOption({ label: "Priest" });
  await page.waitForTimeout(600);
  await page.locator("select").nth(1).selectOption({ label: "Shadow (supported)" });
  await page.waitForTimeout(600);
  await page.locator('input[type="number"]').first().fill("5");
  await page.screenshot({ path: path.join(outDir, "02-configured-shadow-5targets.png"), fullPage: true });

  await page.getByRole("button", { name: "Simulate" }).click();
  await expect(page.getByText("Average DPS")).toBeVisible({ timeout: 120000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(outDir, "03-shadow-results.png"), fullPage: true });
});
