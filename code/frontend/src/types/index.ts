export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  email_verified: boolean;
  has_password?: boolean;
  google_linked?: boolean;
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
  | 'pending'
  | 'rejected'
  | 'applied'
  | 'closed'
  | 'deleted';

export interface UserBrief {
  id: string;
  display_name: string;
  email: string;
}

export interface AssignmentHistoryEntry {
  id: string;
  assignee_id: string | null;
  assignee: UserBrief | null;
  assigned_by: string | null;
  assigned_by_name: string | null;
  created_at: string;
}

export interface ChangeRequest {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  slug: string;
  title: string;
  body: string;
  status: CRStatus;
  author_id: string;
  assignee_id?: string;
  author?: UserBrief | null;
  assignee?: UserBrief | null;
  target_files?: string[];
  closed_at?: string;
  created_at: string;
  updated_at: string;
  comments_count?: number;
  comments?: Comment[];
}

export type BugSeverity = 'critical' | 'major' | 'minor' | 'trivial';

export type BugStatus =
  | 'draft'
  | 'open'
  | 'in_progress'
  | 'resolved'
  | 'wont_fix'
  | 'closed'
  | 'deleted';

export interface Bug {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  slug: string;
  title: string;
  body: string;
  status: BugStatus;
  severity: BugSeverity;
  author_id: string;
  assignee_id?: string;
  author?: UserBrief | null;
  assignee?: UserBrief | null;
  closed_at?: string;
  created_at: string;
  updated_at: string;
  comments_count?: number;
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

export type DocStatus = 'draft' | 'new' | 'changed' | 'synced' | 'deleted';

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

export interface AuditLogUser {
  id: string;
  display_name: string;
  email: string;
}

export interface AuditLogEntry {
  id: string;
  tenant_id: string;
  user_id: string | null;
  user: AuditLogUser | null;
  event_type: string;
  /** Mirrors event_type; kept for a stable, explicit field name in the UI */
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  /** Human-readable label captured at write time (null on legacy entries) */
  entity_label: string | null;
  /** One-line human-readable event description (null on legacy entries) */
  summary: string | null;
  details?: Record<string, unknown> | null;
  created_at: string;
}

export interface SearchResult {
  type: 'project' | 'change_request' | 'bug' | 'document' | 'audit_log';
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
  pages: number;
}

// --- Worker types ---

export type WorkerStatus = 'online' | 'offline' | 'busy';

export interface Worker {
  id: string;
  project_id: string;
  name: string;
  status: WorkerStatus;
  agent: string;
  branch?: string;
  last_heartbeat_at: string | null;
  registered_at: string;
  is_online: boolean;
}

export type JobStatus = 'queued' | 'assigned' | 'running' | 'completed' | 'failed' | 'cancelled';
export type JobType = 'enrich' | 'build' | 'custom';
export type MessageKind = 'output' | 'question' | 'answer';

export interface ChangedFile {
  path: string;
  status: 'new' | 'modified' | 'deleted';
}

export interface WorkerJob {
  id: string;
  project_id: string;
  worker_id?: string;
  worker_name?: string;
  entity_type?: 'change_request' | 'bug' | 'document';
  entity_id?: string;
  entity_title?: string;
  job_type: JobType;
  status: JobStatus;
  agent: string;
  model?: string;
  exit_code?: number;
  created_by: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  changed_files?: ChangedFile[];
}

export interface AgentModel {
  id: string;
  label: string;
}

export interface WorkerJobMessage {
  id: string;
  job_id: string;
  kind: MessageKind;
  content: string;
  sequence: number;
  created_at: string;
}

export interface WorkerJobDetail extends WorkerJob {
  messages: WorkerJobMessage[];
}
