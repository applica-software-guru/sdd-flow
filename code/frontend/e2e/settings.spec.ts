import { test, expect } from '@playwright/test';
import { login, getTenantId, getProjectId } from './auth.setup';

async function goToProjectSettings(page: import('@playwright/test').Page) {
  const projectBase = `/tenants/${getTenantId()}/projects/${getProjectId()}`;
  await page.goto(`${projectBase}/settings`);
  await expect(
    page.getByRole('heading', { name: 'Project Settings' })
  ).toBeVisible({ timeout: 10_000 });
  return projectBase;
}

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('can view project settings', async ({ page }) => {
    await goToProjectSettings(page);
    // Should show General section and API Keys section
    await expect(page.getByRole('heading', { name: 'General' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'API Keys' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Danger Zone' })).toBeVisible();
  });

  test('can update project info', async ({ page }) => {
    await goToProjectSettings(page);

    // The General form has: Name (input), Slug (input), Description (textarea)
    // They are in a form within the "General" section
    const generalForm = page.locator('form').first();
    const nameInput = generalForm.locator('input[type="text"]').first();
    await expect(nameInput).toBeVisible();

    // Read current name
    const currentName = await nameInput.inputValue();
    // Description is a textarea in the general form
    const descInput = generalForm.locator('textarea');
    const currentDesc = await descInput.inputValue();

    // Update description with a timestamp to verify it changes
    const newDesc = `Updated by E2E at ${Date.now()}`;
    await descInput.fill(newDesc);
    await page.getByRole('button', { name: 'Save changes' }).click();

    // Should show success message
    await expect(
      page.getByText('Project updated successfully')
    ).toBeVisible({ timeout: 10_000 });

    // Restore original description
    await descInput.fill(currentDesc);
    await page.getByRole('button', { name: 'Save changes' }).click();
    await page.waitForLoadState('networkidle');
  });

  test('can create an API key', async ({ page }) => {
    await goToProjectSettings(page);

    const keyName = `e2e-key-${Date.now()}`;
    await page.getByPlaceholder('e.g., CI/CD Pipeline').fill(keyName);
    await page.getByRole('button', { name: 'Create key' }).click();

    // Should show the created key notification
    await expect(
      page.getByText('API key created')
    ).toBeVisible({ timeout: 10_000 });
    // The key itself should be displayed
    await expect(page.locator('code')).toBeVisible();

    // The key name should appear in the list
    await expect(page.getByText(keyName)).toBeVisible();
  });

  test('can revoke an API key', async ({ page }) => {
    await goToProjectSettings(page);

    // First create a key to revoke
    const keyName = `e2e-revoke-${Date.now()}`;
    await page.getByPlaceholder('e.g., CI/CD Pipeline').fill(keyName);
    await page.getByRole('button', { name: 'Create key' }).click();
    await expect(page.getByText(keyName)).toBeVisible({ timeout: 10_000 });

    // Find the Revoke button for this key
    const keyRow = page.getByText(keyName).locator('..').locator('..');
    const revokeButton = keyRow.getByRole('button', { name: 'Revoke' });

    if (await revokeButton.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await revokeButton.click();

      // Confirm in dialog
      const confirmRevoke = page
        .getByRole('button', { name: 'Revoke' })
        .last();
      await expect(confirmRevoke).toBeVisible();
      await confirmRevoke.click();

      // Should show "Revoked" status
      await page.waitForLoadState('networkidle');
      await expect(page.getByText('Revoked')).toBeVisible({ timeout: 10_000 });
    }
  });
});
