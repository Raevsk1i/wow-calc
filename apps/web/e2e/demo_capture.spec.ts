import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const OUT = process.env.DEMO_SCREENSHOT_DIR ?? "/opt/cursor/artifacts/screenshots";

test("capture Mage Fire and Devourer sims", async ({ page }) => {
  fs.mkdirSync(OUT, { recursive: true });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "WoW DPS Lab" })).toBeVisible({ timeout: 30_000 });
  await page.screenshot({ path: path.join(OUT, "01-landing-40-specs.png"), fullPage: true });

  const character = page.locator("aside").first();
  const classSelect = character.locator("select").nth(0);
  const specSelect = character.locator("select").nth(1);

  await classSelect.selectOption({ label: "Mage" });
  await expect(specSelect.locator("option", { hasText: "Fire" })).toHaveCount(1, { timeout: 10_000 });
  // Fire Mage Blizzard spec id
  await specSelect.selectOption("63");
  await page.getByRole("button", { name: "5", exact: true }).click();
  await page.getByRole("button", { name: "RUN" }).click();
  await expect(page.getByText("Mean DPS")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Demo / Mock engine result").first()).toBeVisible();

  await page.screenshot({ path: path.join(OUT, "02-mage-fire-5-targets.png"), fullPage: true });

  await classSelect.selectOption({ label: "Demon Hunter" });
  await expect(specSelect.locator("option", { hasText: "Devourer" })).toHaveCount(1, { timeout: 10_000 });
  // Devourer Blizzard spec id
  await specSelect.selectOption("1480");
  await page.getByRole("button", { name: "RUN" }).click();
  await expect(page.getByText("Mean DPS")).toBeVisible({ timeout: 30_000 });
  await page.screenshot({ path: path.join(OUT, "03-devourer-results.png"), fullPage: true });
});

