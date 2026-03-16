import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import { useToast } from '../context/ToastContext';
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
  const { addToast } = useToast();
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
      addToast('Document created', 'success');
    },
    onError: () => {
      addToast('Failed to create document', 'error');
    },
  });
}

export function useUpdateDoc(
  tenantId: string,
  projectId: string,
  docId: string
) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
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
      addToast('Document saved', 'success');
    },
    onError: () => {
      addToast('Failed to save document', 'error');
    },
  });
}

export function useDeleteDoc(
  tenantId: string,
  projectId: string,
  docId: string
) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
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
      addToast('Document deleted', 'success');
    },
    onError: () => {
      addToast('Failed to delete document', 'error');
    },
  });
}
