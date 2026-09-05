import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import type { Notification } from '../types';

interface NotificationFilters {
  unread_only?: boolean;
  page?: number;
  page_size?: number;
}

interface NotificationListResponse {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function useNotifications(filters?: NotificationFilters) {
  return useQuery<NotificationListResponse>({
    queryKey: queryKeys.notifications.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.unread_only) params.set('unread_only', 'true');
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.page_size) params.set('page_size', String(filters.page_size));
      const { data } = await api.get(`/notifications?${params}`);
      return data;
    },
    refetchInterval: 30000,
  });
}

export function useMarkRead(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post(`/notifications/${id}/read`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post('/notifications/read-all');
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

// ---------------------------------------------------------------------------
// Email notification preferences
// ---------------------------------------------------------------------------

export interface NotificationPreference {
  event_type: string;
  email_enabled: boolean;
}

export function useNotificationPreferences() {
  return useQuery<NotificationPreference[]>({
    queryKey: queryKeys.notifications.preferences,
    queryFn: async () => {
      const { data } = await api.get('/notifications/preferences');
      return data;
    },
  });
}

export function useUpdateNotificationPreference() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { event_type: string; email_enabled: boolean }) => {
      const { data } = await api.put('/notifications/preferences', payload);
      return data as NotificationPreference;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.notifications.preferences });
    },
  });
}
