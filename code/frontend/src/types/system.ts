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

export interface AuditLogUser {
  id: string;
  display_name: string;
  email: string;
  avatar_url?: string | null;
}

export interface AuditLogEntry {
  id: string;
  tenant_id: string;
  user_id: string | null;
  user: AuditLogUser | null;
  event_type: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  entity_label: string | null;
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
