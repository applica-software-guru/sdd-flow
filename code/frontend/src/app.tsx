import { lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import LoadingState from '@/components/shared/loading-state';

const Layout = lazy(() => import('@/components/layout'));
const ProtectedRoute = lazy(() => import('@/components/protected-route'));
const SuperUserRoute = lazy(() => import('@/components/super-user-route'));
const LoginPage = lazy(() => import('@/pages/auth/login-page'));
const RegisterPage = lazy(() => import('@/pages/auth/register-page'));
const ForgotPasswordPage = lazy(() => import('@/pages/auth/forgot-password-page'));
const ResetPasswordPage = lazy(() => import('@/pages/auth/reset-password-page'));
const AdminDashboardPage = lazy(() => import('@/pages/admin/dashboard-page'));
const TenantDashboardPage = lazy(() => import('@/pages/tenant/dashboard-page'));
const TenantCreatePage = lazy(() => import('@/pages/tenant/create-page'));
const TenantSettingsPage = lazy(() => import('@/pages/tenant/settings-page'));
const ProfilePage = lazy(() => import('@/pages/system/profile-page'));
const InvitationAcceptPage = lazy(() => import('@/pages/tenant/invitation-accept-page'));
const ProjectCreatePage = lazy(() => import('@/pages/project/create-page'));
const ProjectDashboardPage = lazy(() => import('@/pages/project/dashboard-page'));
const ProjectSettingsPage = lazy(() => import('@/pages/project/settings-page'));
const CRListPage = lazy(() => import('@/pages/change-requests/list-page'));
const CRCreatePage = lazy(() => import('@/pages/change-requests/create-page'));
const CRDetailPage = lazy(() => import('@/pages/change-requests/detail-page'));
const BugListPage = lazy(() => import('@/pages/bugs/list-page'));
const BugCreatePage = lazy(() => import('@/pages/bugs/create-page'));
const BugDetailPage = lazy(() => import('@/pages/bugs/detail-page'));
const DocsTreePage = lazy(() => import('@/pages/docs/tree-page'));
const DocViewPage = lazy(() => import('@/pages/docs/view-page'));
const WorkerJobsListPage = lazy(() => import('@/pages/worker-jobs/list-page'));
const WorkerJobDetailPage = lazy(() => import('@/pages/worker-jobs/detail-page'));
const AuditLogPage = lazy(() => import('@/pages/system/audit-log-page'));
const LandingPage = lazy(() => import('@/pages/system/landing-page'));
const PrivacyPolicyPage = lazy(() => import('@/pages/system/privacy-policy-page'));
const NotFoundPage = lazy(() => import('@/pages/system/not-found-page'));

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense
          fallback={<LoadingState label="Loading page" className="min-h-screen bg-background" />}
        >
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/privacy" element={<PrivacyPolicyPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route
                path="/admin"
                element={
                  <SuperUserRoute>
                    <AdminDashboardPage />
                  </SuperUserRoute>
                }
              />
              <Route path="/tenants" element={<TenantDashboardPage />} />
              <Route path="/tenants/new" element={<TenantCreatePage />} />
              <Route path="/tenants/:tenantId" element={<TenantDashboardPage />} />
              <Route path="/tenants/:tenantId/settings" element={<TenantSettingsPage />} />
              <Route path="/settings/profile" element={<ProfilePage />} />
              <Route
                path="/settings/notifications"
                element={<Navigate to="/settings/profile#notifications" replace />}
              />
              <Route path="/invitations/:token" element={<InvitationAcceptPage />} />
              <Route path="/tenants/:tenantId/audit-log" element={<AuditLogPage />} />
              <Route path="/tenants/:tenantId/projects/new" element={<ProjectCreatePage />} />
              <Route
                path="/tenants/:tenantId/projects/:projectId"
                element={<ProjectDashboardPage />}
              />
              <Route
                path="/tenants/:tenantId/projects/:projectId/settings"
                element={<ProjectSettingsPage />}
              />
              <Route path="/tenants/:tenantId/projects/:projectId/crs" element={<CRListPage />} />
              <Route
                path="/tenants/:tenantId/projects/:projectId/crs/new"
                element={<CRCreatePage />}
              />
              <Route
                path="/tenants/:tenantId/projects/:projectId/crs/:crId"
                element={<CRDetailPage />}
              />
              <Route path="/tenants/:tenantId/projects/:projectId/bugs" element={<BugListPage />} />
              <Route
                path="/tenants/:tenantId/projects/:projectId/bugs/new"
                element={<BugCreatePage />}
              />
              <Route
                path="/tenants/:tenantId/projects/:projectId/bugs/:bugId"
                element={<BugDetailPage />}
              />
              <Route
                path="/tenants/:tenantId/projects/:projectId/workers"
                element={<WorkerJobsListPage />}
              />
              <Route
                path="/tenants/:tenantId/projects/:projectId/workers/:jobId"
                element={<WorkerJobDetailPage />}
              />
              <Route
                path="/tenants/:tenantId/projects/:projectId/docs"
                element={<DocsTreePage />}
              />
              <Route
                path="/tenants/:tenantId/projects/:projectId/docs/:docId"
                element={<DocViewPage />}
              />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
