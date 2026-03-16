import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import { useToast } from '../context/ToastContext';
import type { Tenant, TenantMember } from '../types';

export function useTenants() {
  return useQuery<Tenant[]>({
    queryKey: ['tenants'],
    queryFn: async () => {
      const { data } = await api.get('/tenants');
      return data;
    },
  });
}

export function useTenant(tenantId: string | undefined) {
  return useQuery<Tenant>({
    queryKey: ['tenants', tenantId],
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}`);
      return data;
    },
    enabled: !!tenantId,
  });
}

export function useCreateTenant() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { name: string; slug: string }) => {
      const { data } = await api.post('/tenants', payload);
      return data as Tenant;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      addToast('Tenant created successfully', 'success');
    },
    onError: () => {
      addToast('Failed to create tenant', 'error');
    },
  });
}

export function useUpdateTenant(tenantId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { name?: string; slug?: string }) => {
      const { data } = await api.patch(`/tenants/${tenantId}`, payload);
      return data as Tenant;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      addToast('Tenant settings saved', 'success');
    },
    onError: () => {
      addToast('Failed to save tenant settings', 'error');
    },
  });
}

export function useTenantMembers(tenantId: string | undefined) {
  return useQuery<TenantMember[]>({
    queryKey: ['tenants', tenantId, 'members'],
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/members`);
      return data;
    },
    enabled: !!tenantId,
  });
}

export function useInviteMember(tenantId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: { email: string; role: string }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/members`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'members'],
      });
      addToast('Member invited successfully', 'success');
    },
    onError: () => {
      addToast('Failed to invite member', 'error');
    },
  });
}

export function useRemoveMember(tenantId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (memberId: string) => {
      await api.delete(`/tenants/${tenantId}/members/${memberId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'members'],
      });
      addToast('Member removed', 'success');
    },
    onError: () => {
      addToast('Failed to remove member', 'error');
    },
  });
}
