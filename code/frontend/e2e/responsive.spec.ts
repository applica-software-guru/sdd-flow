import { test, expect } from '@playwright/test';
import { login, getTenantId, getProjectId } from './auth.setup';

test.describe('Responsive layout', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('pages render correctly at mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`/tenants/${getTenantId()}`);

    // Page should load and show heading
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({
      timeout: 10_000,
    });

    // Content should be readable (page didn't crash)
    await expect(page.locator('main')).toBeVisible();
  });

  test('sidebar is hidden on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });

    // Navigate directly to the project page
    await page.goto(`/tenants/${getTenantId()}/projects/${getProjectId()}`);
    await page.waitForURL('**/projects/**');

    // The sidebar <aside> should be hidden on mobile (it uses `hidden lg:block`)
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeHidden();
  });

  test('main content is readable at mobile width', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });

    const projectBase = `/tenants/${getTenantId()}/projects/${getProjectId()}`;

    // Navigate to CR list
    await page.goto(`${projectBase}/crs`);
    await expect(
      page.getByRole('heading', { name: 'Change Requests', exact: true })
    ).toBeVisible({ timeout: 10_000 });

    // The heading should be visible and within the viewport
    const heading = page.getByRole('heading', { name: 'Change Requests', exact: true });
    const box = await heading.boundingBox();
    expect(box).toBeTruthy();
    // Heading should be within viewport width
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(375 + 10); // small tolerance
  });
});
