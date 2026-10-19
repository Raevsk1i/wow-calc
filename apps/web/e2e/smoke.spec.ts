import { expect, test } from "@playwright/test";

test("landing shows brand and simulate CTA", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "WoW DPS Lab" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Simulate" })).toBeVisible();
});
