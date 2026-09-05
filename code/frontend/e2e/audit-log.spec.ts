import { expect, test } from '@playwright/test';
import { getProjectId, getTenantId, login } from './auth.setup';

test.describe('Audit log', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto(`/tenants/${getTenantId()}/audit-log`);
    await expect(page.getByRole('heading', { name: 'Audit Log' })).toBeVisible();
  });

  test('filters entries and expands event details inline', async ({ page }) => {
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10_000 });

    const base = `/api/v1/tenants/${getTenantId()}/projects/${getProjectId()}`;
    const created = await page.request.post(`http://localhost:8000${base}/bugs`, {
      data: { title: 'Expandable audit event', body: 'E2E details', severity: 'major' },
    });
    expect(created.ok()).toBeTruthy();
    const bug = await created.json();
    const transitioned = await page.request.post(
      `http://localhost:8000${base}/bugs/${bug.id}/transition`,
      { data: { status: 'open' } }
    );
    expect(transitioned.ok()).toBeTruthy();

    await page.reload();
    await page.getByLabel('Search activity').fill('bug.transitioned');
    await expect(page.getByText('bug.transitioned', { exact: true }).first()).toBeVisible();

    const expandButton = page
      .getByRole('button', { name: /Expand details for bug\.transitioned/ })
      .first();
    await expandButton.click();
    const details = page.getByRole('region', { name: 'Details for bug.transitioned' });
    await expect(details).toBeVisible();
    const collapseButton = page.getByRole('button', {
      name: /Collapse details for bug\.transitioned/,
    });
    await expect(collapseButton).toHaveAttribute('aria-expanded', 'true');

    await collapseButton.click();
    await expect(details).toBeHidden();
  });
});
