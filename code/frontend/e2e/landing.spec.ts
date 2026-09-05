import { expect, test } from '@playwright/test';
import { login } from './auth.setup';

test.describe('Landing page session behavior', () => {
  test('remains public for anonymous visitors', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveURL('/');
    await expect(
      page.getByRole('heading', { name: /Story Driven Development, managed in the cloud/i })
    ).toBeVisible();
    const navbar = page.getByRole('banner');
    await expect(navbar.getByRole('link', { name: 'Log in' })).toBeVisible();
    await expect(navbar.getByRole('link', { name: 'Sign Up' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Get Started Free' }).first()).toBeVisible();
    await expect(page.getByRole('img', { name: 'Tenant project dashboard preview' })).toBeVisible();
    await expect(
      page.getByRole('img', { name: 'Selected project overview preview' })
    ).toBeVisible();
    await expect(
      page.getByRole('img', { name: 'Shared work-item collaboration preview' })
    ).toBeVisible();
    await expect(
      page.getByRole('img', { name: 'Remote worker orchestration preview' })
    ).toBeVisible();
  });

  test('stays on the landing page and offers an explicit app entry when authenticated', async ({
    page,
  }) => {
    await login(page);
    await page.goto('/');

    const navbar = page.getByRole('banner');
    await expect(navbar.getByRole('link', { name: 'Open app' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Go to dashboard' }).first()).toBeVisible();
    await expect(page).toHaveURL('/');
    await expect(navbar.getByRole('link', { name: 'Log in' })).toHaveCount(0);
    await expect(navbar.getByRole('link', { name: 'Sign Up' })).toHaveCount(0);
    const footer = page.getByRole('contentinfo');
    await expect(footer.getByRole('link', { name: 'Open app' })).toBeVisible();
    await expect(footer.getByRole('link', { name: 'Log in' })).toHaveCount(0);
    await expect(footer.getByRole('link', { name: 'Create account' })).toHaveCount(0);

    await navbar.getByRole('link', { name: 'Open app' }).click();
    await expect(page).toHaveURL('/tenants');
    await expect(page.getByText('Manage your projects and track progress')).toBeVisible();
  });

  test('keeps landing content within a mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    const dimensions = await page.evaluate(() => ({
      viewport: window.innerWidth,
      document: document.documentElement.scrollWidth,
    }));
    expect(dimensions.document).toBeLessThanOrEqual(dimensions.viewport);
  });
});
