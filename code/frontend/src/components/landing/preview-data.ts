export interface PreviewWorkItem {
  id: string;
  title: string;
  kind: 'Change request' | 'Bug';
  status: 'Open' | 'In review' | 'Draft';
  severity?: 'Major';
  author: string;
  comments: number;
}
export interface PreviewWorker {
  name: string;
  agent: string;
  state: 'Online' | 'Busy';
  job: string;
}

export const previewWorkItems: PreviewWorkItem[] = [
  {
    id: 'CR-037',
    title: 'Adopt shared frontend components',
    kind: 'Change request',
    status: 'In review',
    author: 'Maya',
    comments: 6,
  },
  {
    id: 'BUG-011',
    title: 'Keep the landing page public',
    kind: 'Bug',
    status: 'Open',
    severity: 'Major',
    author: 'Alex',
    comments: 3,
  },
  {
    id: 'CR-038',
    title: 'Refresh product previews',
    kind: 'Change request',
    status: 'Draft',
    author: 'Sam',
    comments: 2,
  },
];

export const previewWorkers: PreviewWorker[] = [
  { name: 'Frontend worker', agent: 'Claude', state: 'Busy', job: 'Applying CR-038' },
  { name: 'Quality worker', agent: 'Codex', state: 'Online', job: 'Ready for work' },
];
