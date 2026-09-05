import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { useToast } from '../context/toast';
import type { Comment } from '../types';

export function useComments(
  tenantId: string | undefined,
  projectId: string | undefined,
  entityType: 'change-requests' | 'bugs',
  entityId: string | undefined
) {
  return useQuery<Comment[]>({
    queryKey: queryKeys.comments.all(tenantId, projectId, entityType, entityId),
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
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { body: string }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/${entityType}/${entityId}/comments`,
        payload
      );
      return data as Comment;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.comments.all(tenantId, projectId, entityType, entityId),
      });
      addToast('Comment added', 'success');
    },
    onError: () => {
      addToast('Failed to add comment', 'error');
    },
  });
}

export function useUpdateComment(tenantId: string, projectId: string, commentId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { body: string }) => {
      const { data } = await api.patch(
        `/tenants/${tenantId}/projects/${projectId}/comments/${commentId}`,
        payload
      );
      return data as Comment;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.detail(tenantId, projectId),
      });
      addToast('Comment updated', 'success');
    },
    onError: () => {
      addToast('Failed to update comment', 'error');
    },
  });
}
