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
  });

  test('stays on the landing page and offers an explicit app entry when authenticated', async ({
    page,
  }) => {
    await login(page);
    await page.goto('/');

    await expect(page.getByRole('link', { name: 'Open app' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Go to dashboard' })).toBeVisible();
    await expect(page).toHaveURL('/');
    const navbar = page.getByRole('banner');
    await expect(navbar.getByRole('link', { name: 'Log in' })).toHaveCount(0);
    await expect(navbar.getByRole('link', { name: 'Sign Up' })).toHaveCount(0);

    await page.getByRole('link', { name: 'Open app' }).click();
    await expect(page).toHaveURL('/tenants');
    await expect(page.getByText('Manage your projects and track progress')).toBeVisible();
  });
});
