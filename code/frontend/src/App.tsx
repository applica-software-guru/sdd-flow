import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import TenantDashboardPage from './pages/TenantDashboardPage';
import CreateTenantPage from './pages/CreateTenantPage';
import TenantSettingsPage from './pages/TenantSettingsPage';
import CreateProjectPage from './pages/CreateProjectPage';
import ProjectDashboardPage from './pages/ProjectDashboardPage';
import ProjectSettingsPage from './pages/ProjectSettingsPage';
import CRListPage from './pages/CRListPage';
import CRCreatePage from './pages/CRCreatePage';
import CRDetailPage from './pages/CRDetailPage';
import BugListPage from './pages/BugListPage';
import BugCreatePage from './pages/BugCreatePage';
import BugDetailPage from './pages/BugDetailPage';
import DocsTreePage from './pages/DocsTreePage';
import DocViewPage from './pages/DocViewPage';
import AuditLogPage from './pages/AuditLogPage';
import LandingPage from './pages/LandingPage';
import NotFoundPage from './pages/NotFoundPage';

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

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/tenants" element={<TenantDashboardPage />} />
            <Route path="/tenants/new" element={<CreateTenantPage />} />
            <Route
              path="/tenants/:tenantId"
              element={<TenantDashboardPage />}
            />
            <Route
              path="/tenants/:tenantId/settings"
              element={<TenantSettingsPage />}
            />
            <Route
              path="/tenants/:tenantId/audit-log"
              element={<AuditLogPage />}
            />
            <Route
              path="/tenants/:tenantId/projects/new"
              element={<CreateProjectPage />}
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
