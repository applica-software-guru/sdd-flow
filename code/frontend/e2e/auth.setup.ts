import { Page, APIRequestContext } from '@playwright/test';

let _tenantId: string | null = null;
let _projectId: string | null = null;

/**
 * Log in by registering a test user via the API, creating a tenant and project,
 * and setting the cookies on the browser.
 */
export async function login(page: Page) {
  const email = `e2e-${Date.now()}@test.com`;
  const password = 'TestPassword123!';

  // Register a new user via the backend API
  const resp = await page.request.post('http://localhost:8000/api/v1/auth/register', {
    data: {
      email,
      password,
      display_name: 'E2E Test User',
    },
  });

  if (!resp.ok()) {
    throw new Error(`Failed to register test user: ${resp.status()} ${await resp.text()}`);
  }

  // Extract cookies from response headers
  const allHeaders = resp.headersArray();
  const parsedCookies: Array<{
    name: string;
    value: string;
    domain: string;
    path: string;
  }> = [];

  for (const h of allHeaders) {
    if (h.name.toLowerCase() === 'set-cookie') {
      const match = h.value.match(/^([^=]+)=([^;]*)/);
      if (match) {
        parsedCookies.push({
          name: match[1].trim(),
          value: match[2].trim(),
          domain: 'localhost',
          path: '/',
        });
      }
    }
  }

  if (parsedCookies.length > 0) {
    await page.context().addCookies(parsedCookies);
  }

  // Create a tenant for this test session
  const tenantResp = await page.request.post('http://localhost:8000/api/v1/tenants', {
    data: {
      name: 'E2E Test Tenant',
      slug: `e2e-tenant-${Date.now()}`,
    },
  });
  if (!tenantResp.ok()) {
    throw new Error(`Failed to create tenant: ${tenantResp.status()} ${await tenantResp.text()}`);
  }
  const tenantData = await tenantResp.json();
  _tenantId = tenantData.id;

  // Create a project under the tenant
  const projResp = await page.request.post(
    `http://localhost:8000/api/v1/tenants/${_tenantId}/projects`,
    {
      data: {
        name: 'E2E Test Project',
        slug: `e2e-proj-${Date.now()}`,
        description: 'Project for E2E testing',
      },
    }
  );
  if (!projResp.ok()) {
    throw new Error(`Failed to create project: ${projResp.status()} ${await projResp.text()}`);
  }
  const projData = await projResp.json();
  _projectId = projData.id;

  // Navigate to the app
  await page.goto('/tenants');
  await page.waitForURL('**/tenants**', { timeout: 15_000 });
}

export function getTenantId(): string {
  if (!_tenantId) throw new Error('login() must be called first');
  return _tenantId;
}

export function getProjectId(): string {
  if (!_projectId) throw new Error('login() must be called first');
  return _projectId;
}
