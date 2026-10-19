import { expect, test } from "@playwright/test";

test("landing shows brand and RUN CTA", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "WoW DPS Lab" })).toBeVisible();
  await expect(page.getByRole("button", { name: "RUN" })).toBeVisible();
  await expect(page.getByText(/13 classes|Coverage/i)).toBeVisible();
});
