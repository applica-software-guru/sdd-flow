import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import type { AuditLogEntry, PaginatedResponse } from '../types';

interface AuditLogFilters {
  action?: string;
  entity_type?: string;
  user_id?: string;
  from?: string;
  to?: string;
  page?: number;
  page_size?: number;
}

export function useAuditLog(tenantId: string | undefined, filters?: AuditLogFilters) {
  return useQuery<PaginatedResponse<AuditLogEntry>>({
    queryKey: queryKeys.audit.list(tenantId, filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.set('action', filters.action);
      if (filters?.entity_type) params.set('entity_type', filters.entity_type);
      if (filters?.user_id) params.set('user_id', filters.user_id);
      if (filters?.from) params.set('from', filters.from);
      if (filters?.to) params.set('to', filters.to);
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.page_size) params.set('page_size', String(filters.page_size));
      const { data } = await api.get(`/tenants/${tenantId}/audit-log?${params}`);
      return data;
    },
    enabled: !!tenantId,
  });
}
