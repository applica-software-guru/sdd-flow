import { Navigate, useLocation } from 'react-router-dom';
import { useCurrentUser } from '../hooks/useAuth';

export default function ProtectedRoute({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: user, isLoading, isError } = useCurrentUser();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (isError || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
