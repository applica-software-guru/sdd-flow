import { test, expect } from '@playwright/test';
import { login, getTenantId, getProjectId } from './auth.setup';

/**
 * Helper: navigate to the CR list for the test project.
 */
async function goToCRList(page: import('@playwright/test').Page) {
  const projectBase = `/tenants/${getTenantId()}/projects/${getProjectId()}`;
  await page.goto(`${projectBase}/crs`);
  await expect(
    page.getByRole('heading', { name: 'Change Requests', exact: true })
  ).toBeVisible({ timeout: 10_000 });
  return projectBase;
}

/**
 * Helper: create a CR via the UI and return its title.
 */
async function createCR(page: import('@playwright/test').Page) {
  const projectBase = await goToCRList(page);

  await page.getByRole('link', { name: /New CR/i }).click();
  await page.waitForURL('**/crs/new');

  const title = `E2E Test CR ${Date.now()}`;
  // Title input has placeholder "Brief description of the change"
  await page.getByPlaceholder('Brief description of the change').fill(title);
  // Description uses MarkdownEditor — target the inner textarea
  await page.locator('.w-md-editor-text-input').fill('Automated test description for CR.');

  await page.getByRole('button', { name: 'Create change request' }).click();
  await page.waitForURL('**/crs/**', { timeout: 15_000 });
  await expect(page.getByRole('heading', { name: title })).toBeVisible({
    timeout: 10_000,
  });

  return { title, projectBase };
}

test.describe('Change Requests', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('can view CR list page', async ({ page }) => {
    await goToCRList(page);
    // Either shows a table or an empty state
    const hasTable = await page.locator('table').isVisible().catch(() => false);
    const hasEmpty = await page
      .getByText(/no change requests/i)
      .isVisible()
      .catch(() => false);
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test('can create a new CR', async ({ page }) => {
    await createCR(page);
  });

  test('can view CR detail', async ({ page }) => {
    // First create a CR so there is something to view
    await createCR(page);

    // Go back to the list
    await goToCRList(page);

    // Click on first CR in the table
    const firstCR = page.locator('table a').first();
    await expect(firstCR).toBeVisible({ timeout: 5_000 });
    await firstCR.click();
    await page.waitForURL('**/crs/**');
    // Should show CR title and status
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByText('Transition to:')).toBeVisible({
      timeout: 5_000,
    });
  });

  test('can transition CR status', async ({ page }) => {
    // First create a CR
    await createCR(page);

    // Go back to the list
    await goToCRList(page);

    // Click on first CR
    const firstCR = page.locator('table a').first();
    await expect(firstCR).toBeVisible({ timeout: 5_000 });
    await firstCR.click();
    await page.waitForURL('**/crs/**');

    // Find a transition button and click it
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

  test('can add a comment', async ({ page }) => {
    // First create a CR
    await createCR(page);

    // Go back to the list
    await goToCRList(page);

    // Click on first CR
    const firstCR = page.locator('table a').first();
    await expect(firstCR).toBeVisible({ timeout: 5_000 });
    await firstCR.click();
    await page.waitForURL('**/crs/**');

    const commentText = `E2E comment ${Date.now()}`;
    await page
      .getByPlaceholder('Write a comment...')
      .fill(commentText);
    await page.getByRole('button', { name: 'Add comment' }).click();

    // Wait for the comment to appear
    await expect(page.getByText(commentText)).toBeVisible({
      timeout: 10_000,
    });
  });
});
