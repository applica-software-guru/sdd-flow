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
