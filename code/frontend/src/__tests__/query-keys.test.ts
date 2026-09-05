import { describe, expect, it } from 'vitest';
import { queryKeys } from '@/api/query-keys';

describe('queryKeys', () => {
  it('keeps resource keys hierarchical', () => {
    expect(queryKeys.bugs.detail('tenant', 'project', 'bug')).toEqual([
      'tenants',
      'tenant',
      'projects',
      'project',
      'bugs',
      'bug',
    ]);
    expect(queryKeys.bugs.assignments('tenant', 'project', 'bug')).toEqual([
      'tenants',
      'tenant',
      'projects',
      'project',
      'bugs',
      'bug',
      'assignments',
    ]);
  });

  it('uses list filters only below the collection key', () => {
    const filters = { status: 'open' };
    expect(queryKeys.changeRequests.list('tenant', 'project', filters)).toEqual([
      'tenants',
      'tenant',
      'projects',
      'project',
      'crs',
      filters,
    ]);
  });
});
