import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import LoadingState from '@/components/shared/loading-state';
import { useCurrentUser } from '@/hooks/use-auth';

export default function SuperUserRoute({ children }: { children: ReactNode }) {
  const { data: user, isLoading } = useCurrentUser();
  if (isLoading) return <LoadingState label="Checking platform authorization" />;
  if (user?.platform_role !== 'super_user') return <Navigate to="/tenants" replace />;
  return children;
}
