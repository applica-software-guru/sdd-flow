export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  email_verified: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface TenantMember {
  id: string;
  user_id: string;
  email: string;
  display_name: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
}

export interface Project {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  description?: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  total_crs: number;
  open_crs: number;
  total_bugs: number;
  open_bugs: number;
  total_docs: number;
}

export type CRStatus =
  | 'draft'
  | 'approved'
  | 'rejected'
  | 'applied'
  | 'closed';

export interface ChangeRequest {
  id: string;
  project_id: string;
  title: string;
  body: string;
  status: CRStatus;
  author_id: string;
  assignee_id?: string;
  target_files?: string[];
  closed_at?: string;
  created_at: string;
  updated_at: string;
  comments?: Comment[];
}

export type BugSeverity = 'critical' | 'major' | 'minor' | 'trivial';

export type BugStatus =
  | 'open'
  | 'in_progress'
  | 'resolved'
  | 'wont_fix'
  | 'closed';

export interface Bug {
  id: string;
  project_id: string;
  title: string;
  body: string;
  status: BugStatus;
  severity: BugSeverity;
  author_id: string;
  assignee_id?: string;
  closed_at?: string;
  created_at: string;
  updated_at: string;
  comments?: Comment[];
}

export interface Comment {
  id: string;
  body: string;
  author_id: string;
  author: User;
  entity_type: 'change_request' | 'bug';
  entity_id: string;
  created_at: string;
  updated_at: string;
}

export type DocStatus = 'new' | 'changed' | 'synced' | 'deleted';

export interface DocumentFile {
  id: string;
  project_id: string;
  title: string;
  path: string;
  content: string;
  status: DocStatus;
  version: number;
  last_modified_by?: string;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  tenant_id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  title: string;
  read_at: string | null;
  created_at: string;
}

export interface ApiKey {
  id: string;
  project_id: string;
  name: string;
  key_prefix: string;
  full_key?: string; // only returned on creation
  created_by: string;
  last_used_at?: string;
  revoked_at?: string;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  tenant_id: string;
  user_id: string;
  user: User;
  action: string;
  entity_type: string;
  entity_id: string;
  details?: Record<string, unknown>;
  created_at: string;
}

export interface SearchResult {
  type: 'project' | 'change_request' | 'bug' | 'document';
  id: string;
  title: string;
  snippet?: string;
  url: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
