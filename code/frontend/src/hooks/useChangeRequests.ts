import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import { useToast } from '../context/ToastContext';
import type { ChangeRequest, PaginatedResponse } from '../types';

interface CRFilters {
  status?: string;
  author_id?: string;
  assignee_id?: string;
  page?: number;
  page_size?: number;
}

export function useChangeRequests(
  tenantId: string | undefined,
  projectId: string | undefined,
  filters?: CRFilters
) {
  return useQuery<PaginatedResponse<ChangeRequest>>({
    queryKey: ['tenants', tenantId, 'projects', projectId, 'crs', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set('status', filters.status);
      if (filters?.author_id) params.set('author_id', filters.author_id);
      if (filters?.assignee_id) params.set('assignee_id', filters.assignee_id);
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.page_size)
        params.set('page_size', String(filters.page_size));
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/change-requests?${params}`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId,
  });
}

export function useChangeRequest(
  tenantId: string | undefined,
  projectId: string | undefined,
  crId: string | undefined
) {
  return useQuery<ChangeRequest>({
    queryKey: ['tenants', tenantId, 'projects', projectId, 'crs', crId],
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/change-requests/${crId}`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId && !!crId,
  });
}

export function useCreateCR(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: {
      title: string;
      body: string;
      assignee_id?: string;
    }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/change-requests`,
        payload
      );
      return data as ChangeRequest;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'crs'],
      });
      addToast('Change request created', 'success');
    },
    onError: () => {
      addToast('Failed to create change request', 'error');
    },
  });
}

export function useUpdateCR(
  tenantId: string,
  projectId: string,
  crId: string
) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: {
      title?: string;
      body?: string;
      assignee_id?: string;
    }) => {
      const { data } = await api.patch(
        `/tenants/${tenantId}/projects/${projectId}/change-requests/${crId}`,
        payload
      );
      return data as ChangeRequest;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'crs'],
      });
      addToast('Change request updated', 'success');
    },
    onError: () => {
      addToast('Failed to update change request', 'error');
    },
  });
}

export function useTransitionCR(
  tenantId: string,
  projectId: string,
  crId: string
) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { status: string }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/change-requests/${crId}/transition`,
        payload
      );
      return data as ChangeRequest;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'crs'],
      });
      addToast('Status updated', 'success');
    },
    onError: () => {
      addToast('Failed to update status', 'error');
    },
  });
}
