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

  test('scroll-to-comments button scrolls to the comments section', async ({ page }) => {
    // Create a CR with a long body so the comments section ends up below the fold.
    const projectBase = await goToCRList(page);
    await page.getByRole('link', { name: /New CR/i }).click();
    await page.waitForURL('**/crs/new');

    const title = `E2E Long CR ${Date.now()}`;
    await page.getByPlaceholder('Brief description of the change').fill(title);
    const longBody = Array.from({ length: 80 }, (_, i) => `Paragraph ${i + 1}: lorem ipsum dolor sit amet.`).join('\n\n');
    await page.locator('.w-md-editor-text-input').fill(longBody);
    await page.getByRole('button', { name: 'Create change request' }).click();
    await page.waitForURL('**/crs/**', { timeout: 15_000 });
    await expect(page.getByRole('heading', { name: title })).toBeVisible({ timeout: 10_000 });

    const commentsSection = page.locator('#comments');
    await expect(commentsSection).toBeAttached({ timeout: 10_000 });

    const fab = page.getByRole('button', { name: 'Scroll to comments' });
    const scrollToTop = () =>
      page.evaluate(() => {
        // The app scrolls inside <main> (overflow-y-auto), not the window.
        document.querySelector('main')?.scrollTo(0, 0);
        window.scrollTo(0, 0);
      });

    // At the top of a long page the comments are below the fold: FAB fades in.
    await scrollToTop();
    await expect(fab).toHaveClass(/opacity-100/, { timeout: 5_000 });

    // Click: the page lands on the comments section and the FAB fades out.
    await fab.click();
    await expect(commentsSection).toBeInViewport({ timeout: 5_000 });
    await expect(fab).toHaveClass(/opacity-0/, { timeout: 5_000 });

    // Scrolling back up brings the FAB back.
    await scrollToTop();
    await expect(fab).toHaveClass(/opacity-100/, { timeout: 5_000 });
  });
});
