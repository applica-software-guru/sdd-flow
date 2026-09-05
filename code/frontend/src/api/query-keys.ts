const tenantRoot = (tenantId?: string) => ['tenants', tenantId] as const;
const projectRoot = (tenantId?: string, projectId?: string) =>
  [...tenantRoot(tenantId), 'projects', projectId] as const;

export const queryKeys = {
  auth: { me: ['auth', 'me'] as const },
  tenants: {
    all: ['tenants'] as const,
    navigation: ['tenants', 'navigation'] as const,
    detail: (tenantId?: string) => tenantRoot(tenantId),
    dashboard: (tenantId?: string) => [...tenantRoot(tenantId), 'dashboard'] as const,
    members: (tenantId?: string) => [...tenantRoot(tenantId), 'members'] as const,
    invitations: (tenantId?: string) => [...tenantRoot(tenantId), 'invitations'] as const,
    invitation: (token?: string) => ['invitation-verify', token] as const,
  },
  projects: {
    all: (tenantId?: string) => [...tenantRoot(tenantId), 'projects'] as const,
    detail: projectRoot,
  },
  bugs: {
    all: (tenantId?: string, projectId?: string) =>
      [...projectRoot(tenantId, projectId), 'bugs'] as const,
    list: (tenantId?: string, projectId?: string, filters?: object) =>
      [...queryKeys.bugs.all(tenantId, projectId), filters] as const,
    detail: (tenantId?: string, projectId?: string, bugId?: string) =>
      [...queryKeys.bugs.all(tenantId, projectId), bugId] as const,
    assignments: (tenantId?: string, projectId?: string, bugId?: string) =>
      [...queryKeys.bugs.detail(tenantId, projectId, bugId), 'assignments'] as const,
  },
  changeRequests: {
    all: (tenantId?: string, projectId?: string) =>
      [...projectRoot(tenantId, projectId), 'crs'] as const,
    list: (tenantId?: string, projectId?: string, filters?: object) =>
      [...queryKeys.changeRequests.all(tenantId, projectId), filters] as const,
    detail: (tenantId?: string, projectId?: string, crId?: string) =>
      [...queryKeys.changeRequests.all(tenantId, projectId), crId] as const,
    assignments: (tenantId?: string, projectId?: string, crId?: string) =>
      [...queryKeys.changeRequests.detail(tenantId, projectId, crId), 'assignments'] as const,
  },
  docs: {
    all: (tenantId?: string, projectId?: string) =>
      [...projectRoot(tenantId, projectId), 'docs'] as const,
    list: (tenantId?: string, projectId?: string, filters?: object) =>
      [...queryKeys.docs.all(tenantId, projectId), filters] as const,
    detail: (tenantId?: string, projectId?: string, docId?: string) =>
      [...queryKeys.docs.all(tenantId, projectId), docId] as const,
  },
  workers: {
    all: (tenantId?: string, projectId?: string) =>
      [...projectRoot(tenantId, projectId), 'workers'] as const,
    jobs: (tenantId?: string, projectId?: string) =>
      [...projectRoot(tenantId, projectId), 'worker-jobs'] as const,
    jobList: (tenantId?: string, projectId?: string, filters?: object) =>
      [...queryKeys.workers.jobs(tenantId, projectId), filters] as const,
    job: (tenantId?: string, projectId?: string, jobId?: string) =>
      [...queryKeys.workers.jobs(tenantId, projectId), jobId] as const,
    models: (tenantId?: string, projectId?: string) =>
      [...projectRoot(tenantId, projectId), 'agent-models'] as const,
  },
  comments: {
    all: (tenantId?: string, projectId?: string, entityType?: string, entityId?: string) =>
      [...projectRoot(tenantId, projectId), entityType, entityId, 'comments'] as const,
    project: projectRoot,
  },
  notifications: {
    all: ['notifications'] as const,
    list: (filters?: object) => ['notifications', filters] as const,
    preferences: ['notification-preferences'] as const,
  },
  audit: {
    list: (tenantId?: string, filters?: object) =>
      [...tenantRoot(tenantId), 'audit-log', filters] as const,
  },
  apiKeys: {
    all: (tenantId?: string, projectId?: string) =>
      [...projectRoot(tenantId, projectId), 'api-keys'] as const,
  },
  search: {
    list: (tenantId?: string, query?: string, type?: string) =>
      ['search', tenantId, query, type] as const,
  },
};
