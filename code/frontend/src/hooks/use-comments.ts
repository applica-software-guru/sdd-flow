import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { useToast } from '../context/toast';
import type { Comment } from '../types';
import { translate } from '@/i18n';

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
      addToast(translate('common:auto.comment_added'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_add_comment'), 'error');
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
      addToast(translate('common:auto.comment_updated'), 'success');
    },
    onError: () => {
      addToast(translate('common:auto.failed_to_update_comment'), 'error');
    },
  });
}
