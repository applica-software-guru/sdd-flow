import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { DocumentFile } from '../types';

export function useDocs(
  tenantId: string | undefined,
  projectId: string | undefined
) {
  return useQuery<DocumentFile[]>({
    queryKey: ['tenants', tenantId, 'projects', projectId, 'docs'],
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/docs`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId,
  });
}

export function useDoc(
  tenantId: string | undefined,
  projectId: string | undefined,
  docId: string | undefined
) {
  return useQuery<DocumentFile>({
    queryKey: ['tenants', tenantId, 'projects', projectId, 'docs', docId],
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/docs/${docId}`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId && !!docId,
  });
}

export function useCreateDoc(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      title: string;
      path: string;
      content: string;
      parent_id?: string;
      status?: string;
    }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/docs`,
        payload
      );
      return data as DocumentFile;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'docs'],
      });
    },
  });
}

export function useUpdateDoc(
  tenantId: string,
  projectId: string,
  docId: string
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      title?: string;
      content?: string;
      status?: string;
    }) => {
      const { data } = await api.patch(
        `/tenants/${tenantId}/projects/${projectId}/docs/${docId}`,
        payload
      );
      return data as DocumentFile;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'docs'],
      });
    },
  });
}

export function useDeleteDoc(
  tenantId: string,
  projectId: string,
  docId: string
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.delete(
        `/tenants/${tenantId}/projects/${projectId}/docs/${docId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'docs'],
      });
    },
  });
}
