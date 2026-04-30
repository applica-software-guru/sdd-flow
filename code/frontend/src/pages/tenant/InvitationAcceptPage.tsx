import { useEffect } from 'react';
import { Link, Navigate, useLocation, useNavigate, useParams } from 'react-router-dom';
import { useCurrentUser } from '../../hooks/useAuth';
import { getApiErrorMessage, useAcceptInvitation, useVerifyInvitation } from '../../hooks/useTenants';
import PageContainer from '../../components/PageContainer';

export default function InvitationAcceptPage() {
  const { token } = useParams<{ token: string }>();
  const location = useLocation();
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const navigate = useNavigate();
  const verification = useVerifyInvitation(token ?? '');
  const acceptInvitation = useAcceptInvitation(token ?? '');

  useEffect(() => {
    if (acceptInvitation.isSuccess) {
      navigate('/tenants', { replace: true });
    }
  }, [acceptInvitation.isSuccess, navigate]);

  if (!token) {
    return (
      <PageContainer className="py-16 text-center">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Invalid invitation link</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">The invitation token is missing.</p>
      </PageContainer>
    );
  }

  if (userLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (acceptInvitation.isError) {
    return (
      <PageContainer>
        <div className="rounded-lg border border-red-200 bg-white p-8 text-center shadow-sm dark:border-red-800 dark:bg-slate-800">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Invitation could not be accepted</h1>
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">
            {getApiErrorMessage(acceptInvitation.error, 'Failed to accept invitation')}
          </p>
          <div className="mt-6">
            <Link
              to="/tenants"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Go to tenants
            </Link>
          </div>
        </div>
      </PageContainer>
    );
  }

  if (verification.isLoading) {
    return (
      <PageContainer>
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Verifying invitation</h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Please wait while we verify your invitation.</p>
          <div className="mt-6 flex items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        </div>
      </PageContainer>
    );
  }

  if (verification.isError) {
    return (
      <PageContainer>
        <div className="rounded-lg border border-red-200 bg-white p-8 text-center shadow-sm dark:border-red-800 dark:bg-slate-800">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Invalid invitation</h1>
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">
            {getApiErrorMessage(verification.error, 'This invitation is not valid')}
          </p>
          <div className="mt-6">
            <Link
              to="/tenants"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Go to tenants
            </Link>
          </div>
        </div>
      </PageContainer>
    );
  }

  const info = verification.data;

  return (
    <PageContainer>
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">You have been invited</h1>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
          You have been invited to join <span className="font-semibold text-slate-900 dark:text-slate-100">{info?.tenant_name}</span> as <span className="font-semibold text-slate-900 dark:text-slate-100">{info?.role}</span>.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            onClick={() => acceptInvitation.mutate()}
            disabled={acceptInvitation.isPending}
            className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {acceptInvitation.isPending ? 'Accepting...' : 'Accept invitation'}
          </button>
          <Link
            to="/tenants"
            className="rounded-md border border-slate-300 bg-white px-5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
          >
            Decline
          </Link>
        </div>
      </div>
    </PageContainer>
  );
}
