import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { useToast } from '../context/toast';
import type { AssignmentHistoryEntry, ChangeRequest, PaginatedResponse } from '../types';

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
    queryKey: queryKeys.changeRequests.list(tenantId, projectId, filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set('status', filters.status);
      if (filters?.author_id) params.set('author_id', filters.author_id);
      if (filters?.assignee_id) params.set('assignee_id', filters.assignee_id);
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.page_size) params.set('page_size', String(filters.page_size));
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
    queryKey: queryKeys.changeRequests.detail(tenantId, projectId, crId),
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
      slug?: string;
      assignee_id?: string;
    }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/change-requests`,
        payload
      );
      return data as ChangeRequest;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.changeRequests.all(tenantId, projectId),
      });
      addToast('Change request created', 'success');
    },
    onError: () => {
      addToast('Failed to create change request', 'error');
    },
  });
}

export function useUpdateCR(tenantId: string, projectId: string, crId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: {
      title?: string;
      body?: string;
      slug?: string;
      assignee_id?: string;
    }) => {
      const { data } = await api.patch(
        `/tenants/${tenantId}/projects/${projectId}/change-requests/${crId}`,
        payload
      );
      return data as ChangeRequest;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.changeRequests.all(tenantId, projectId),
      });
      addToast('Change request updated', 'success');
    },
    onError: () => {
      addToast('Failed to update change request', 'error');
    },
  });
}

export function useTransitionCR(tenantId: string, projectId: string, crId: string) {
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
      void queryClient.invalidateQueries({
        queryKey: queryKeys.changeRequests.all(tenantId, projectId),
      });
      addToast('Status updated', 'success');
    },
    onError: () => {
      addToast('Failed to update status', 'error');
    },
  });
}

export function useAssignCR(tenantId: string, projectId: string, crId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { assignee_id: string | null }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/change-requests/${crId}/assign`,
        payload
      );
      return data as ChangeRequest;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.changeRequests.all(tenantId, projectId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.changeRequests.assignments(tenantId, projectId, crId),
      });
      addToast('Assignee updated', 'success');
    },
    onError: () => {
      addToast('Failed to update assignee', 'error');
    },
  });
}

export function useCRAssignments(
  tenantId: string | undefined,
  projectId: string | undefined,
  crId: string | undefined
) {
  return useQuery<AssignmentHistoryEntry[]>({
    queryKey: queryKeys.changeRequests.assignments(tenantId, projectId, crId),
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/change-requests/${crId}/assignments`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId && !!crId,
  });
}
