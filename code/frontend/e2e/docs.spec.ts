import { test, expect } from '@playwright/test';
import { login, getTenantId, getProjectId } from './auth.setup';

async function goToDocsPage(page: import('@playwright/test').Page) {
  const projectBase = `/tenants/${getTenantId()}/projects/${getProjectId()}`;
  await page.goto(`${projectBase}/docs`);
  await expect(
    page.getByRole('heading', { name: 'Documentation' })
  ).toBeVisible({ timeout: 10_000 });
  return projectBase;
}

/**
 * Helper: create a document via the UI and return its title.
 */
async function createDoc(page: import('@playwright/test').Page) {
  const projectBase = await goToDocsPage(page);

  await page.getByRole('button', { name: /New Document/i }).click();
  await expect(
    page.getByRole('heading', { name: 'Create New Document' })
  ).toBeVisible();

  const docTitle = `E2E Doc ${Date.now()}`;
  // Title input has placeholder "Getting Started"
  await page.getByPlaceholder('Getting Started').fill(docTitle);
  // Path input has placeholder "guides/getting-started"
  await page.getByPlaceholder('guides/getting-started').fill(`e2e/test-doc-${Date.now()}`);

  await page.getByRole('button', { name: 'Create' }).click();
  await page.waitForLoadState('networkidle');
  await expect(page.getByText(docTitle)).toBeVisible({ timeout: 10_000 });

  return { docTitle, projectBase };
}

async function createDocInFolder(
  page: import('@playwright/test').Page,
  folder: string,
  titleSuffix: string
) {
  const projectBase = await goToDocsPage(page);

  await page.getByRole('button', { name: /New Document/i }).click();
  await expect(
    page.getByRole('heading', { name: 'Create New Document' })
  ).toBeVisible();

  const docTitle = `E2E Doc ${titleSuffix} ${Date.now()}`;
  await page.getByPlaceholder('Getting Started').fill(docTitle);
  await page
    .getByPlaceholder('guides/getting-started')
    .fill(`${folder}/test-doc-${Date.now()}`);

  await page.getByRole('button', { name: 'Create' }).click();
  await page.waitForLoadState('networkidle');
  await expect(page.getByText(docTitle)).toBeVisible({ timeout: 10_000 });

  return { docTitle, projectBase };
}

test.describe('Docs', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('can view docs tree page', async ({ page }) => {
    await goToDocsPage(page);
    // Either shows document list or empty state
    const hasDocs = await page
      .locator('a[href*="/docs/"]')
      .first()
      .isVisible()
      .catch(() => false);
    const hasEmpty = await page
      .getByText(/no documents/i)
      .isVisible()
      .catch(() => false);
    expect(hasDocs || hasEmpty).toBeTruthy();
  });

  test('can create a new document', async ({ page }) => {
    await createDoc(page);
  });

  test('groups documents by folder and filters with search', async ({ page }) => {
    const folderName = `e2e-group-${Date.now()}`;
    const { docTitle } = await createDocInFolder(page, folderName, 'Grouped');

    await goToDocsPage(page);

    await expect(page.getByRole('button', { name: new RegExp(folderName) })).toBeVisible({
      timeout: 10_000,
    });

    await page.getByPlaceholder('Search by title or path').fill(folderName);
    await expect(page.getByText(docTitle)).toBeVisible({ timeout: 10_000 });
  });

  test('can view a document', async ({ page }) => {
    // First create a document so there is something to view
    await createDoc(page);

    // Navigate back to docs list
    await goToDocsPage(page);

    // Click on the first document link
    const firstDoc = page.locator('a[href*="/docs/"]').first();
    await expect(firstDoc).toBeVisible({ timeout: 5_000 });
    await firstDoc.click();
    await page.waitForURL('**/docs/**');
    // Should show the doc title
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    // Should show Edit and Delete buttons
    await expect(
      page.getByRole('button', { name: 'Edit' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Delete' })
    ).toBeVisible();
  });

  test('can edit a document', async ({ page }) => {
    // First create a document so there is something to edit
    await createDoc(page);

    // Navigate back to docs list
    await goToDocsPage(page);

    const firstDoc = page.locator('a[href*="/docs/"]').first();
    await expect(firstDoc).toBeVisible({ timeout: 5_000 });
    await firstDoc.click();
    await page.waitForURL('**/docs/**');

    // Click Edit
    await page.getByRole('button', { name: 'Edit' }).click();

    // The editing form should now be visible — Title is an input[type="text"], Content uses MarkdownEditor
    // Wait for the title input to appear (first text input in the edit form)
    const titleInput = page.locator('form input[type="text"]');
    await expect(titleInput).toBeVisible();
    // Content is a MarkdownEditor — the inner textarea has class .w-md-editor-text-input
    const contentEditor = page.locator('.w-md-editor-text-input');
    await expect(contentEditor).toBeVisible();

    // Modify content
    const updatedContent = `Updated by E2E test at ${Date.now()}`;
    await contentEditor.fill(updatedContent);

    // Save
    await page.getByRole('button', { name: 'Save' }).click();
    await page.waitForLoadState('networkidle');

    // Should exit edit mode and show the updated content
    await expect(page.getByText(updatedContent)).toBeVisible({
      timeout: 10_000,
    });
  });

  test('can delete a document', async ({ page }) => {
    // First create a doc we can safely delete
    await createDoc(page);

    // Navigate back to docs list
    await goToDocsPage(page);

    // Navigate to the first doc
    const firstDoc = page.locator('a[href*="/docs/"]').first();
    await expect(firstDoc).toBeVisible({ timeout: 5_000 });
    await firstDoc.click();
    await page.waitForURL('**/docs/**');

    // Click Delete
    await page.getByRole('button', { name: 'Delete' }).click();

    // Confirm in the dialog — the ConfirmDialog has confirmLabel="Delete"
    // There are now two "Delete" buttons: one on the page (hidden behind dialog) and one in the dialog
    const confirmButton = page.getByRole('button', { name: 'Delete' }).last();
    await expect(confirmButton).toBeVisible();
    await confirmButton.click();

    // Should redirect back to docs list
    await page.waitForURL('**/docs', { timeout: 10_000 });
    await expect(
      page.getByRole('heading', { name: 'Documentation' })
    ).toBeVisible();
  });
});
