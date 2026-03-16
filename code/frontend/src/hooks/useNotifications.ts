import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
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
    queryKey: ['notifications', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.unread_only)
        params.set('unread_only', 'true');
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.page_size)
        params.set('page_size', String(filters.page_size));
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
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
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
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}
