import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type { SearchResult } from '../types';

export type SearchTypeFilter = 'project' | 'doc' | 'cr' | 'bug' | 'audit_log';

export function useSearch(
  tenantId: string | undefined,
  query: string,
  type?: SearchTypeFilter
) {
  return useQuery<SearchResult[]>({
    queryKey: ['search', tenantId, query, type],
    queryFn: async () => {
      const params = new URLSearchParams({ q: query });
      if (type) params.set('type', type);
      const { data } = await api.get(
        `/tenants/${tenantId}/search?${params}`
      );
      return (data.results ?? data).map((r: Record<string, unknown>) => ({
        type: r.entity_type ?? r.type,
        id: r.entity_id ?? r.id,
        title: r.title,
        snippet: r.snippet,
        project_id: r.project_id,
        url: buildUrl(tenantId!, r),
      }));
    },
    enabled: !!tenantId && query.length >= 2,
    staleTime: 10000,
  });
}

export function buildUrl(tenantId: string, result: Record<string, unknown>): string {
  const type = (result.entity_type ?? result.type) as string;
  const id = (result.entity_id ?? result.id) as string;
  const projectId = result.project_id as string | undefined;
  const base = `/tenants/${tenantId}`;

  switch (type) {
    case 'project':
      return `${base}/projects/${id}`;
    case 'document':
      return `${base}/projects/${projectId}/docs/${id}`;
    case 'change_request':
      return `${base}/projects/${projectId}/crs/${id}`;
    case 'bug':
      return `${base}/projects/${projectId}/bugs/${id}`;
    case 'audit_log':
      return `${base}/audit-log`;
    default:
      return base;
  }
}
