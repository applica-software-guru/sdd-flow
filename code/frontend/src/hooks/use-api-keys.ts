import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { useToast } from '../context/toast';
import type { ApiKey } from '../types';

export function useApiKeys(tenantId: string | undefined, projectId: string | undefined) {
  return useQuery<ApiKey[]>({
    queryKey: queryKeys.apiKeys.all(tenantId, projectId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/projects/${projectId}/api-keys`);
      return data;
    },
    enabled: !!tenantId && !!projectId,
  });
}

export function useCreateApiKey(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { name: string }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/api-keys`,
        payload
      );
      return data as ApiKey;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.apiKeys.all(tenantId, projectId),
      });
      addToast('API key created', 'success');
    },
    onError: () => {
      addToast('Failed to create API key', 'error');
    },
  });
}

export function useRevokeApiKey(tenantId: string, projectId: string, keyId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async () => {
      await api.delete(`/tenants/${tenantId}/projects/${projectId}/api-keys/${keyId}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.apiKeys.all(tenantId, projectId),
      });
      addToast('API key revoked', 'success');
    },
    onError: () => {
      addToast('Failed to revoke API key', 'error');
    },
  });
}
