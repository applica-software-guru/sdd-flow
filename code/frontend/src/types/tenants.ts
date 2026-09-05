export interface Tenant {
  id: string;
  name: string;
  slug: string;
  owner_id?: string;
  role?: 'owner' | 'admin' | 'member' | 'viewer';
  created_at: string;
  updated_at: string;
}

export interface WorkspaceNavigationProject {
  id: string;
  name: string;
  slug: string;
  archived_at: string | null;
}

export interface WorkspaceNavigationTenant {
  id: string;
  name: string;
  slug: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  can_create_project: boolean;
  projects: WorkspaceNavigationProject[];
}

export interface WorkspaceNavigationResponse {
  tenants: WorkspaceNavigationTenant[];
}

export interface TenantDashboardWindow {
  preset: 'last_7_days' | 'last_30_days' | 'last_90_days';
  from: string;
  to: string;
}

export interface TenantDashboardKpis {
  active_projects: number;
  archived_projects: number;
  documents_total: number;
  documents_synced: number;
  documents_pending: number;
  docs_sync_percentage: number;
  open_bugs: number;
  critical_bugs: number;
  major_bugs: number;
  active_crs: number;
  review_queue_crs: number;
  comments_in_window: number;
  distinct_commenters_in_window: number;
  activity_events_in_window: number;
  workers_online: number;
  workers_total: number;
}

export interface TenantDashboardProjectStats {
  documents_total: number;
  documents_synced: number;
  documents_pending: number;
  open_bugs: number;
  critical_bugs: number;
  major_bugs: number;
  active_crs: number;
  review_queue_crs: number;
  comments_in_window: number;
  distinct_commenters_in_window: number;
  activity_events_in_window: number;
  workers_online: number;
  workers_total: number;
  last_activity_at: string | null;
}

export interface TenantDashboardProject {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  archived_at: string | null;
  stats: TenantDashboardProjectStats;
}

export interface TenantDashboardSummary {
  tenant: { id: string; name: string; slug: string };
  window: TenantDashboardWindow;
  kpis: TenantDashboardKpis;
  projects: TenantDashboardProject[];
}

export interface TenantMember {
  id: string;
  user_id: string;
  email: string;
  display_name: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
}

export interface TenantInvitation {
  id: string;
  tenant_id: string;
  email: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
  status: 'pending' | 'accepted' | 'expired';
}
