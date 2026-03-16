import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { Comment } from '../types';

export function useComments(
  tenantId: string | undefined,
  projectId: string | undefined,
  entityType: 'change-requests' | 'bugs',
  entityId: string | undefined
) {
  return useQuery<Comment[]>({
    queryKey: ['tenants', tenantId, 'projects', projectId, entityType, entityId, 'comments'],
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/${entityType}/${entityId}/comments`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId && !!entityId,
  });
}

export function useAddComment(
  tenantId: string,
  projectId: string,
  entityType: 'change-requests' | 'bugs',
  entityId: string
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { body: string }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/${entityType}/${entityId}/comments`,
        payload
      );
      return data as Comment;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [
          'tenants',
          tenantId,
          'projects',
          projectId,
          entityType,
          entityId,
          'comments',
        ],
      });
    },
  });
}

export function useUpdateComment(
  tenantId: string,
  projectId: string,
  commentId: string
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { body: string }) => {
      const { data } = await api.patch(
        `/tenants/${tenantId}/projects/${projectId}/comments/${commentId}`,
        payload
      );
      return data as Comment;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId],
      });
    },
  });
}
