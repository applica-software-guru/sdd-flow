import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { User } from '../types';

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const { data } = await api.get('/auth/me');
      return data;
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const { data } = await api.post('/auth/login', credentials);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async (payload: {
      email: string;
      password: string;
      display_name: string;
    }) => {
      const { data } = await api.post('/auth/register', payload);
      return data;
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post('/auth/logout');
    },
    onSuccess: () => {
      queryClient.clear();
    },
  });
}
