import { expect, test } from '@playwright/test';
import { getTenantId, login } from './auth.setup';

test('applies dark mode before the application paints', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('theme', 'dark'));
  await page.goto('/login');

  await expect(page.locator('html')).toHaveClass(/dark/);
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('content', '#020617');

  const backgrounds = await page.evaluate(() => ({
    html: getComputedStyle(document.documentElement).backgroundColor,
    body: getComputedStyle(document.body).backgroundColor,
    root: getComputedStyle(document.querySelector('#root')!).backgroundColor,
  }));
  expect(new Set(Object.values(backgrounds))).toEqual(new Set(['rgb(2, 8, 23)']));
});

test('preserves the dark app shell while a lazy route loads', async ({ page }) => {
  await login(page);
  await page.evaluate(() => localStorage.setItem('theme', 'dark'));
  await page.reload();
  await page.route('**/src/pages/system/audit-log-page.tsx*', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 400));
    await route.continue();
  });

  await page.getByRole('link', { name: 'Audit Log' }).click();
  await expect(page.getByText('SDD Flow', { exact: true })).toBeVisible();
  await expect(page.locator('html')).toHaveClass(/dark/);
  await expect(page.getByRole('heading', { name: 'Audit Log' })).toBeVisible();

  await page.getByRole('button', { name: /Search/ }).click();
  const searchDialog = page.getByRole('dialog', { name: 'Global search' });
  await expect(searchDialog).toBeVisible();
  await expect(searchDialog).toHaveCSS('background-color', 'rgb(30, 41, 59)');

  const escapeHint = searchDialog.getByText('Esc', { exact: true });
  const closeButton = searchDialog.getByRole('button', { name: 'Close' });
  const [escapeBox, closeBox] = await Promise.all([
    escapeHint.boundingBox(),
    closeButton.boundingBox(),
  ]);
  expect(escapeBox).not.toBeNull();
  expect(closeBox).not.toBeNull();
  expect(escapeBox!.x + escapeBox!.width).toBeLessThan(closeBox!.x);
  await expect(page).toHaveURL(`/tenants/${getTenantId()}/audit-log`);
});
