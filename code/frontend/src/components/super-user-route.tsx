import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import LoadingState from '@/components/shared/loading-state';
import { useCurrentUser } from '@/hooks/use-auth';
import { translate } from '@/i18n';

export default function SuperUserRoute({ children }: { children: ReactNode }) {
  const { data: user, isLoading } = useCurrentUser();
  if (isLoading)
    return <LoadingState label={translate('common:auto.checking_platform_authorization')} />;
  if (user?.platform_role !== 'super_user') return <Navigate to="/tenants" replace />;
  return children;
}
