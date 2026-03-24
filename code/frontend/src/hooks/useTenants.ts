import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { AxiosError } from 'axios';
import api from '../lib/api';
import { useToast } from '../context/ToastContext';
import type { Tenant, TenantInvitation, TenantMember } from '../types';

type ApiErrorResponse = { detail?: string };

export function getApiErrorMessage(error: unknown, fallback: string): string {
  const axiosError = error as AxiosError<ApiErrorResponse>;
  const detail = axiosError.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail;
  }
  return fallback;
}

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

export function useTenantInvitations(tenantId: string | undefined) {
  return useQuery<TenantInvitation[]>({
    queryKey: ['tenants', tenantId, 'invitations'],
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
      const { data } = await api.post(
        `/tenants/${tenantId}/invitations`,
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'members'],
      });
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'invitations'],
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
    queryKey: ['invitation-verify', token],
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
      queryClient.refetchQueries({ queryKey: ['tenants'] });
      addToast('Invitation accepted', 'success');
    },
    onError: (error) => {
      addToast(getApiErrorMessage(error, 'Failed to accept invitation'), 'error');
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
