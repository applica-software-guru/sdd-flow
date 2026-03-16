import { describe, it, expect } from 'vitest';
import { buildUrl } from '../hooks/useSearch';

const TENANT_ID = 'tenant-abc-123';
const PROJECT_ID = 'proj-456';

describe('buildUrl', () => {
  it('builds correct URL for project results', () => {
    const result = { entity_type: 'project', entity_id: 'p1', project_id: 'p1' };
    expect(buildUrl(TENANT_ID, result)).toBe(`/tenants/${TENANT_ID}/projects/p1`);
  });

  it('builds correct URL for document results', () => {
    const result = { entity_type: 'document', entity_id: 'd1', project_id: PROJECT_ID };
    expect(buildUrl(TENANT_ID, result)).toBe(
      `/tenants/${TENANT_ID}/projects/${PROJECT_ID}/docs/d1`
    );
  });

  it('builds correct URL for change_request results', () => {
    const result = { entity_type: 'change_request', entity_id: 'cr1', project_id: PROJECT_ID };
    expect(buildUrl(TENANT_ID, result)).toBe(
      `/tenants/${TENANT_ID}/projects/${PROJECT_ID}/crs/cr1`
    );
  });

  it('builds correct URL for bug results', () => {
    const result = { entity_type: 'bug', entity_id: 'b1', project_id: PROJECT_ID };
    expect(buildUrl(TENANT_ID, result)).toBe(
      `/tenants/${TENANT_ID}/projects/${PROJECT_ID}/bugs/b1`
    );
  });

  it('builds correct URL for audit_log results', () => {
    const result = { entity_type: 'audit_log', entity_id: 'a1' };
    expect(buildUrl(TENANT_ID, result)).toBe(`/tenants/${TENANT_ID}/audit-log`);
  });

  it('falls back to tenant base URL for unknown type', () => {
    const result = { entity_type: 'unknown', entity_id: 'x1' };
    expect(buildUrl(TENANT_ID, result)).toBe(`/tenants/${TENANT_ID}`);
  });

  it('handles legacy field names (type/id instead of entity_type/entity_id)', () => {
    const result = { type: 'bug', id: 'b2', project_id: PROJECT_ID };
    expect(buildUrl(TENANT_ID, result)).toBe(
      `/tenants/${TENANT_ID}/projects/${PROJECT_ID}/bugs/b2`
    );
  });
});
