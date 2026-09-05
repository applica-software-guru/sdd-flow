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

export interface ApiKey {
  id: string;
  project_id: string;
  name: string;
  key_prefix: string;
  full_key?: string;
  created_by: string;
  last_used_at?: string;
  revoked_at?: string;
  created_at: string;
}
