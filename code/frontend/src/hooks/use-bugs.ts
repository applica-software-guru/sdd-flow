import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { useToast } from '../context/toast';
import type { AssignmentHistoryEntry, Bug, PaginatedResponse } from '../types';
import { translate } from '@/i18n';

interface BugFilters {
  status?: string;
  severity?: string;
  author_id?: string;
  assignee_id?: string;
  page?: number;
  page_size?: number;
}

export function useBugs(
  tenantId: string | undefined,
  projectId: string | undefined,
  filters?: BugFilters
) {
  return useQuery<PaginatedResponse<Bug>>({
    queryKey: queryKeys.bugs.list(tenantId, projectId, filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set('status', filters.status);
      if (filters?.severity) params.set('severity', filters.severity);
      if (filters?.author_id) params.set('author_id', filters.author_id);
      if (filters?.assignee_id) params.set('assignee_id', filters.assignee_id);
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.page_size) params.set('page_size', String(filters.page_size));
      const { data } = await api.get(`/tenants/${tenantId}/projects/${projectId}/bugs?${params}`);
      return data;
    },
    enabled: !!tenantId && !!projectId,
  });
}

export function useBug(
  tenantId: string | undefined,
  projectId: string | undefined,
  bugId: string | undefined
) {
  return useQuery<Bug>({
    queryKey: queryKeys.bugs.detail(tenantId, projectId, bugId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/projects/${projectId}/bugs/${bugId}`);
      return data;
    },
    enabled: !!tenantId && !!projectId && !!bugId,
  });
}

export function useCreateBug(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: {
      title: string;
      body: string;
      slug?: string;
      severity: string;
      assignee_id?: string;
    }) => {
      const { data } = await api.post(`/tenants/${tenantId}/projects/${projectId}/bugs`, payload);
      return data as Bug;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bugs.all(tenantId, projectId),
      });
      addToast(translate('common:auto.bug_reported_successfully'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_report_bug'), 'error');
    },
  });
}

export function useUpdateBug(tenantId: string, projectId: string, bugId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: {
      title?: string;
      body?: string;
      slug?: string;
      severity?: string;
      assignee_id?: string;
    }) => {
      const { data } = await api.patch(
        `/tenants/${tenantId}/projects/${projectId}/bugs/${bugId}`,
        payload
      );
      return data as Bug;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bugs.all(tenantId, projectId),
      });
      addToast(translate('common:auto.bug_updated'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_update_bug'), 'error');
    },
  });
}

export function useTransitionBug(tenantId: string, projectId: string, bugId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { status: string }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/bugs/${bugId}/transition`,
        payload
      );
      return data as Bug;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bugs.all(tenantId, projectId),
      });
      addToast(translate('common:auto.status_updated'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_update_status'), 'error');
    },
  });
}

export function useAssignBug(tenantId: string, projectId: string, bugId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { assignee_id: string | null }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/bugs/${bugId}/assign`,
        payload
      );
      return data as Bug;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bugs.all(tenantId, projectId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bugs.assignments(tenantId, projectId, bugId),
      });
      addToast(translate('common:auto.assignee_updated'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_update_assignee'), 'error');
    },
  });
}

export function useBugAssignments(
  tenantId: string | undefined,
  projectId: string | undefined,
  bugId: string | undefined
) {
  return useQuery<AssignmentHistoryEntry[]>({
    queryKey: queryKeys.bugs.assignments(tenantId, projectId, bugId),
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/bugs/${bugId}/assignments`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId && !!bugId,
  });
}
