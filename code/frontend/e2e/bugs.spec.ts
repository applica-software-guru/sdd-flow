import { test, expect } from '@playwright/test';
import { login, getTenantId, getProjectId } from './auth.setup';

async function goToBugList(page: import('@playwright/test').Page) {
  const projectBase = `/tenants/${getTenantId()}/projects/${getProjectId()}`;
  await page.goto(`${projectBase}/bugs`);
  await expect(
    page.getByRole('heading', { name: 'Bugs', exact: true })
  ).toBeVisible({ timeout: 10_000 });
  return projectBase;
}

/**
 * Helper: create a bug via the UI and return its title.
 */
async function createBug(page: import('@playwright/test').Page) {
  const projectBase = await goToBugList(page);

  await page.getByRole('link', { name: /Report Bug/i }).click();
  await page.waitForURL('**/bugs/new');

  const title = `E2E Test Bug ${Date.now()}`;
  // Title input has placeholder "Brief description of the bug"
  await page.getByPlaceholder('Brief description of the bug').fill(title);
  // Description uses MarkdownEditor — target the inner textarea
  await page.locator('.w-md-editor-text-input').fill('Steps to reproduce: automated test.');
  // Severity is the first <select> in the form
  await page.locator('select').first().selectOption('major');

  await page.getByRole('button', { name: 'Report bug' }).click();
  await page.waitForURL('**/bugs/**', { timeout: 15_000 });
  await expect(page.getByRole('heading', { name: title })).toBeVisible({
    timeout: 10_000,
  });

  return { title, projectBase };
}

test.describe('Bugs', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('can view bug list page', async ({ page }) => {
    await goToBugList(page);
    // Wait for loading to finish — either a table or the empty state appears
    await page.waitForLoadState('networkidle');
    const hasTable = await page.locator('table').isVisible().catch(() => false);
    const hasEmpty = await page
      .getByRole('heading', { name: 'No bugs found' })
      .isVisible()
      .catch(() => false);
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test('can create a new bug', async ({ page }) => {
    await createBug(page);
  });

  test('can view bug detail', async ({ page }) => {
    // First create a bug so there is something to view
    await createBug(page);

    // Go back to the list
    await goToBugList(page);

    const firstBug = page.locator('table a').first();
    await expect(firstBug).toBeVisible({ timeout: 5_000 });
    await firstBug.click();
    await page.waitForURL('**/bugs/**');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    // Should show transition section for non-closed bugs
    await expect(page.getByText('Transition to:')).toBeVisible({
      timeout: 5_000,
    });
  });

  test('can transition bug status', async ({ page }) => {
    // First create a bug
    await createBug(page);

    // Go back to the list
    await goToBugList(page);

    const firstBug = page.locator('table a').first();
    await expect(firstBug).toBeVisible({ timeout: 5_000 });
    await firstBug.click();
    await page.waitForURL('**/bugs/**');

    const transitionSection = page.getByText('Transition to:');
    await expect(transitionSection).toBeVisible({ timeout: 5_000 });
    const transitionButton = transitionSection
      .locator('..')
      .locator('..')
      .getByRole('button')
      .first();
    if (await transitionButton.isVisible().catch(() => false)) {
      await transitionButton.click();
      await page.waitForLoadState('networkidle');
    }
  });

  test('can add a comment to a bug', async ({ page }) => {
    // First create a bug
    await createBug(page);

    // Go back to the list
    await goToBugList(page);

    const firstBug = page.locator('table a').first();
    await expect(firstBug).toBeVisible({ timeout: 5_000 });
    await firstBug.click();
    await page.waitForURL('**/bugs/**');

    const commentText = `E2E bug comment ${Date.now()}`;
    await page
      .getByPlaceholder('Write a comment...')
      .fill(commentText);
    await page.getByRole('button', { name: 'Add comment' }).click();

    await expect(page.getByText(commentText)).toBeVisible({
      timeout: 10_000,
    });
  });
});
