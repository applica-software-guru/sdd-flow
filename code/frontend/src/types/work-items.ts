import type { User, UserBrief } from './auth';

export type CRStatus = 'draft' | 'pending' | 'rejected' | 'applied' | 'closed' | 'deleted';
export type BugSeverity = 'critical' | 'major' | 'minor' | 'trivial';
export type BugStatus =
  'draft' | 'open' | 'in_progress' | 'resolved' | 'wont_fix' | 'closed' | 'deleted';

export interface AssignmentHistoryEntry {
  id: string;
  assignee_id: string | null;
  assignee: UserBrief | null;
  assigned_by: string | null;
  assigned_by_name: string | null;
  created_at: string;
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

interface WorkItemBase {
  id: string;
  project_id: string;
  number: number;
  formatted_number: string;
  slug: string;
  title: string;
  body: string;
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

export interface ChangeRequest extends WorkItemBase {
  status: CRStatus;
  target_files?: string[];
}

export interface Bug extends WorkItemBase {
  status: BugStatus;
  severity: BugSeverity;
}
