import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { useToast } from '../context/toast';
import type { DocumentFile } from '../types';
import { translate } from '@/i18n';

export function useDocs(
  tenantId: string | undefined,
  projectId: string | undefined,
  filters?: { status?: string }
) {
  return useQuery<DocumentFile[]>({
    queryKey: queryKeys.docs.list(tenantId, projectId, filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set('status', filters.status);
      const query = params.toString();
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/docs${query ? `?${query}` : ''}`
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
    queryKey: queryKeys.docs.detail(tenantId, projectId, docId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/projects/${projectId}/docs/${docId}`);
      return data;
    },
    enabled: !!tenantId && !!projectId && !!docId,
  });
}

export function useCreateDoc(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: {
      title: string;
      path: string;
      content: string;
      parent_id?: string;
      status?: string;
    }) => {
      const { data } = await api.post(`/tenants/${tenantId}/projects/${projectId}/docs`, payload);
      return data as DocumentFile;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.docs.all(tenantId, projectId),
      });
      addToast(translate('common:auto.document_created'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_create_document'), 'error');
    },
  });
}

export function useUpdateDoc(tenantId: string, projectId: string, docId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: {
      title?: string;
      content?: string;
      status?: string;
      path?: string;
    }) => {
      const { data } = await api.patch(
        `/tenants/${tenantId}/projects/${projectId}/docs/${docId}`,
        payload
      );
      return data as DocumentFile;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.docs.all(tenantId, projectId),
      });
      addToast(translate('common:auto.document_saved'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_save_document'), 'error');
    },
  });
}

export function useDeleteDoc(tenantId: string, projectId: string, docId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async () => {
      await api.delete(`/tenants/${tenantId}/projects/${projectId}/docs/${docId}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.docs.all(tenantId, projectId),
      });
      addToast(translate('common:auto.document_deleted'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_delete_document'), 'error');
    },
  });
}
