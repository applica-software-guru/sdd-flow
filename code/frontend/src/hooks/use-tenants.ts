import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../api/query-keys';
import api from '../api/client';
import { getApiErrorMessage } from '../api/errors';
import { useToast } from '../context/toast';
import type { Tenant, TenantDashboardSummary, TenantInvitation, TenantMember } from '../types';

export function useTenants() {
  return useQuery<Tenant[]>({
    queryKey: queryKeys.tenants.all,
    queryFn: async () => {
      const { data } = await api.get('/tenants');
      return data;
    },
  });
}

export function useTenant(tenantId: string | undefined) {
  return useQuery<Tenant>({
    queryKey: queryKeys.tenants.detail(tenantId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}`);
      return data;
    },
    enabled: !!tenantId,
  });
}

export function useTenantDashboard(tenantId: string | undefined) {
  return useQuery<TenantDashboardSummary>({
    queryKey: queryKeys.tenants.dashboard(tenantId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/dashboard`);
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
      void queryClient.invalidateQueries({ queryKey: queryKeys.tenants.all });
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
      void queryClient.invalidateQueries({ queryKey: queryKeys.tenants.all });
      addToast('Tenant settings saved', 'success');
    },
    onError: () => {
      addToast('Failed to save tenant settings', 'error');
    },
  });
}

export function useTenantMembers(tenantId: string | undefined) {
  return useQuery<TenantMember[]>({
    queryKey: queryKeys.tenants.members(tenantId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/members`);
      return data;
    },
    enabled: !!tenantId,
  });
}

export function useTenantInvitations(tenantId: string | undefined) {
  return useQuery<TenantInvitation[]>({
    queryKey: queryKeys.tenants.invitations(tenantId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/invitations`);
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
      const { data } = await api.post(`/tenants/${tenantId}/invitations`, payload);
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.members(tenantId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.invitations(tenantId),
      });
      addToast('Member invited successfully', 'success');
    },
    onError: (error) => {
      addToast(getApiErrorMessage(error, 'Failed to invite member'), 'error');
    },
  });
}

export type InvitationVerification = {
  email: string;
  role: string;
  tenant_name: string;
  expires_at: string;
};

export function useVerifyInvitation(token: string) {
  return useQuery<InvitationVerification>({
    queryKey: queryKeys.tenants.invitation(token),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/invitations/${token}/verify`);
      return data;
    },
    enabled: !!token,
    retry: false,
  });
}

export function useAcceptInvitation(token: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/tenants/invitations/${token}/accept`);
      return data;
    },
    onSuccess: () => {
      void queryClient.refetchQueries({ queryKey: queryKeys.tenants.all });
      addToast('Invitation accepted', 'success');
    },
    onError: (error) => {
      addToast(getApiErrorMessage(error, 'Failed to accept invitation'), 'error');
    },
  });
}

export function useCancelInvitation(tenantId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (invitationId: string) => {
      await api.delete(`/tenants/${tenantId}/invitations/${invitationId}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.invitations(tenantId),
      });
      addToast('Invitation cancelled', 'success');
    },
    onError: () => {
      addToast('Failed to cancel invitation', 'error');
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
      void queryClient.invalidateQueries({
        queryKey: queryKeys.tenants.members(tenantId),
      });
      addToast('Member removed', 'success');
    },
    onError: () => {
      addToast('Failed to remove member', 'error');
    },
  });
}
