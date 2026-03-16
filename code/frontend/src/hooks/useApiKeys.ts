import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { ApiKey } from '../types';

export function useApiKeys(
  tenantId: string | undefined,
  projectId: string | undefined
) {
  return useQuery<ApiKey[]>({
    queryKey: ['tenants', tenantId, 'projects', projectId, 'api-keys'],
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/api-keys`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId,
  });
}

export function useCreateApiKey(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { name: string }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/api-keys`,
        payload
      );
      return data as ApiKey;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'api-keys'],
      });
    },
  });
}

export function useRevokeApiKey(
  tenantId: string,
  projectId: string,
  keyId: string
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.delete(
        `/tenants/${tenantId}/projects/${projectId}/api-keys/${keyId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'api-keys'],
      });
    },
  });
}
