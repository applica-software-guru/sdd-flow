export type WorkerStatus = 'online' | 'offline' | 'busy';
export type JobStatus = 'queued' | 'assigned' | 'running' | 'completed' | 'failed' | 'cancelled';
export type JobType = 'enrich' | 'build' | 'custom';
export type MessageKind = 'output' | 'question' | 'answer';

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
