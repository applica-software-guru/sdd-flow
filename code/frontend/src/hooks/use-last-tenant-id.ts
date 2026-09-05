import { useEffect } from 'react';

const KEY = 'sdd-last-tenant-id';

function readStoredTenant(): string | undefined {
  try {
    return localStorage.getItem(KEY) ?? undefined;
  } catch {
    return undefined;
  }
}

export function useLastTenantId(tenantId?: string): string | undefined {
  useEffect(() => {
    if (!tenantId) return;
    try {
      localStorage.setItem(KEY, tenantId);
    } catch {
      /* storage is optional */
    }
  }, [tenantId]);
  return tenantId ?? readStoredTenant();
}
