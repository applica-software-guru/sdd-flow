import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type { SearchResult } from '../types';

export function useSearch(
  tenantId: string | undefined,
  query: string,
  type?: string
) {
  return useQuery<SearchResult[]>({
    queryKey: ['search', tenantId, query, type],
    queryFn: async () => {
      const params = new URLSearchParams({ q: query });
      if (type) params.set('type', type);
      const { data } = await api.get(
        `/tenants/${tenantId}/search?${params}`
      );
      return data;
    },
    enabled: !!tenantId && query.length >= 2,
    staleTime: 10000,
  });
}
