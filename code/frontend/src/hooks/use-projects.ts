import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { useToast } from '../context/toast';
import type { Project } from '../types';

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
      addToast('Project created successfully', 'success');
    },
    onError: () => {
      addToast('Failed to create project', 'error');
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
      addToast('Project settings saved', 'success');
    },
    onError: () => {
      addToast('Failed to save project settings', 'error');
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
      addToast('Project archived', 'success');
    },
    onError: () => {
      addToast('Failed to archive project', 'error');
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
      addToast('Project restored', 'success');
    },
    onError: () => {
      addToast('Failed to restore project', 'error');
    },
  });
}
