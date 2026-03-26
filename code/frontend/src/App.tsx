import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import TenantDashboardPage from './pages/tenant/DashboardPage';
import TenantCreatePage from './pages/tenant/CreatePage';
import TenantSettingsPage from './pages/tenant/SettingsPage';
import InvitationAcceptPage from './pages/tenant/InvitationAcceptPage';
import ProjectCreatePage from './pages/project/CreatePage';
import ProjectDashboardPage from './pages/project/DashboardPage';
import ProjectSettingsPage from './pages/project/SettingsPage';
import CRListPage from './pages/change-requests/ListPage';
import CRCreatePage from './pages/change-requests/CreatePage';
import CRDetailPage from './pages/change-requests/DetailPage';
import BugListPage from './pages/bugs/ListPage';
import BugCreatePage from './pages/bugs/CreatePage';
import BugDetailPage from './pages/bugs/DetailPage';
import DocsTreePage from './pages/docs/TreePage';
import DocViewPage from './pages/docs/ViewPage';
import WorkerJobsListPage from './pages/worker-jobs/ListPage';
import WorkerJobDetailPage from './pages/worker-jobs/DetailPage';
import AuditLogPage from './pages/system/AuditLogPage';
import LandingPage from './pages/system/LandingPage';
import NotFoundPage from './pages/system/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password/:token" element={<ResetPasswordPage />} />

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/tenants" element={<TenantDashboardPage />} />
            <Route path="/tenants/new" element={<TenantCreatePage />} />
            <Route
              path="/tenants/:tenantId"
              element={<TenantDashboardPage />}
            />
            <Route
              path="/tenants/:tenantId/settings"
              element={<TenantSettingsPage />}
            />
            <Route
              path="/invitations/:token"
              element={<InvitationAcceptPage />}
            />
            <Route
              path="/tenants/:tenantId/audit-log"
              element={<AuditLogPage />}
            />
            <Route
              path="/tenants/:tenantId/projects/new"
              element={<ProjectCreatePage />}
            />
            <Route
              path="/tenants/:tenantId/projects/:projectId"
              element={<ProjectDashboardPage />}
            />
            <Route
              path="/tenants/:tenantId/projects/:projectId/settings"
              element={<ProjectSettingsPage />}
            />
            <Route
              path="/tenants/:tenantId/projects/:projectId/crs"
              element={<CRListPage />}
            />
            <Route
              path="/tenants/:tenantId/projects/:projectId/crs/new"
              element={<CRCreatePage />}
            />
            <Route
              path="/tenants/:tenantId/projects/:projectId/crs/:crId"
              element={<CRDetailPage />}
            />
            <Route
              path="/tenants/:tenantId/projects/:projectId/bugs"
              element={<BugListPage />}
            />
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

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
