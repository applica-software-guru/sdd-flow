import { useQuery } from '@tanstack/react-query';
import api from '@/api/client';

export type AdminTab = 'users' | 'tenants' | 'projects' | 'audit-log';

export interface AdminOverview {
  users_count: number;
  tenants_count: number;
  projects_count: number;
  recent_login_count: number;
  recent_failed_login_count: number;
  recent_events: Array<{ id: string; event_type: string; created_at: string }>;
}

export interface AdminPage {
  items: Array<Record<string, unknown>>;
  total: number;
  page: number;
  pages: number;
}

export function useAdminOverview() {
  return useQuery<AdminOverview>({
    queryKey: ['admin', 'overview'],
    queryFn: async () => (await api.get('/admin/overview')).data,
  });
}

export function useAdminList(tab: AdminTab, page: number, search: string) {
  return useQuery<AdminPage>({
    queryKey: ['admin', tab, page, search],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: '25' });
      if (search && tab !== 'audit-log') params.set('search', search);
      if (search && tab === 'audit-log') params.set('event_type', search);
      return (await api.get(`/admin/${tab}?${params}`)).data;
    },
  });
}
