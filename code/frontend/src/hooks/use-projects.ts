import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { useToast } from '../context/toast';
import type { Project } from '../types';
import { translate } from '@/i18n';

export function useProjects(tenantId: string | undefined) {
  return useQuery<Project[]>({
    queryKey: queryKeys.projects.all(tenantId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/projects`);
      return data;
    },
    enabled: !!tenantId,
  });
}

export function useProject(tenantId: string | undefined, projectId: string | undefined) {
  return useQuery<Project>({
    queryKey: queryKeys.projects.detail(tenantId, projectId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/projects/${projectId}`);
      return data;
    },
    enabled: !!tenantId && !!projectId,
  });
}

export function useCreateProject(tenantId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { name: string; slug: string; description?: string }) => {
      const { data } = await api.post(`/tenants/${tenantId}/projects`, payload);
      return data as Project;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.all(tenantId),
      });
      addToast(translate('common:auto.project_created_successfully'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_create_project'), 'error');
    },
  });
}

export function useUpdateProject(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { name?: string; slug?: string; description?: string }) => {
      const { data } = await api.patch(`/tenants/${tenantId}/projects/${projectId}`, payload);
      return data as Project;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.all(tenantId),
      });
      addToast(translate('common:auto.project_settings_saved'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_save_project_settings'), 'error');
    },
  });
}

export function useArchiveProject(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/tenants/${tenantId}/projects/${projectId}/archive`);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.all(tenantId),
      });
      addToast(translate('common:auto.project_archived'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_archive_project'), 'error');
    },
  });
}

export function useRestoreProject(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/tenants/${tenantId}/projects/${projectId}/restore`);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.all(tenantId),
      });
      addToast(translate('common:auto.project_restored'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_restore_project'), 'error');
    },
  });
}
