import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { Project } from '../types';

export function useProjects(tenantId: string | undefined) {
  return useQuery<Project[]>({
    queryKey: ['tenants', tenantId, 'projects'],
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/projects`);
      return data;
    },
    enabled: !!tenantId,
  });
}

export function useProject(
  tenantId: string | undefined,
  projectId: string | undefined
) {
  return useQuery<Project>({
    queryKey: ['tenants', tenantId, 'projects', projectId],
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId,
  });
}

export function useCreateProject(tenantId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      name: string;
      slug: string;
      description?: string;
    }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects`,
        payload
      );
      return data as Project;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects'],
      });
    },
  });
}

export function useUpdateProject(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      name?: string;
      slug?: string;
      description?: string;
    }) => {
      const { data } = await api.patch(
        `/tenants/${tenantId}/projects/${projectId}`,
        payload
      );
      return data as Project;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects'],
      });
    },
  });
}

export function useArchiveProject(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/archive`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects'],
      });
    },
  });
}

export function useRestoreProject(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/restore`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects'],
      });
    },
  });
}
