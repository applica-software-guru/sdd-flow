import { test, expect } from '@playwright/test';
import { login, getTenantId, getProjectId } from './auth.setup';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('can navigate to tenant dashboard', async ({ page }) => {
    await page.goto(`/tenants/${getTenantId()}`);
    await expect(
      page.getByRole('heading', { level: 1 })
    ).toBeVisible({ timeout: 10_000 });
    // Should show tenant name or "Dashboard"
    await expect(page.getByText('Manage your projects')).toBeVisible();
  });

  test('can navigate to a project overview', async ({ page }) => {
    await page.goto(`/tenants/${getTenantId()}/projects/${getProjectId()}`);
    await page.waitForURL(`**/projects/**`);
    // Project dashboard page should show an overview heading or content
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 10_000 });

    // Project context bar and breadcrumb should make active project obvious
    await expect(page.getByText('Project context')).toBeVisible();
    await expect(page.getByText('Project: E2E Test Project')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Projects' })).toBeVisible();
    await expect(page.getByText('Overview')).toBeVisible();
  });

  test('sidebar links work for CR list, Bug list, Docs, Settings', async ({
    page,
  }) => {
    // Navigate directly to the project
    await page.goto(`/tenants/${getTenantId()}/projects/${getProjectId()}`);
    await page.waitForURL(`**/projects/**`);

    // The sidebar is only visible on lg+ screens; set viewport wide enough
    await page.setViewportSize({ width: 1280, height: 800 });

    // Navigate to Change Requests via sidebar
    const crLink = page.locator('aside a', { hasText: 'Change Requests' });
    await expect(crLink).toBeVisible({ timeout: 5_000 });
    await crLink.click();
    await page.waitForURL('**/crs');
    await expect(
      page.getByRole('heading', { name: 'Change Requests', exact: true })
    ).toBeVisible({ timeout: 10_000 });

    // Navigate to Bugs via sidebar
    const bugsLink = page.locator('aside a', { hasText: 'Bugs' });
    await bugsLink.click();
    await page.waitForURL('**/bugs');
    await expect(
      page.getByRole('heading', { name: 'Bugs' })
    ).toBeVisible();

    // Navigate to Docs via sidebar
    const docsLink = page.locator('aside a', { hasText: 'Docs' });
    await docsLink.click();
    await page.waitForURL('**/docs');
    await expect(
      page.getByRole('heading', { name: 'Documentation' })
    ).toBeVisible();

    // Navigate to Settings via sidebar (project-level settings link is the 2nd "Settings")
    const settingsLinks = page.locator('aside a', { hasText: 'Settings' });
    // The second Settings link in the sidebar is the project settings
    await settingsLinks.last().click();
    await page.waitForURL('**/settings');
    await expect(
      page.getByRole('heading', { name: 'Project Settings' })
    ).toBeVisible();
  });
});
