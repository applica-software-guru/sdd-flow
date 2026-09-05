import { formatDateOnly } from '@/lib/format';
import { useState, FormEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  useProject,
  useUpdateProject,
  useArchiveProject,
  useRestoreProject,
} from '../../hooks/use-projects';
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from '../../hooks/use-api-keys';
import ConfirmDialog from '../../components/confirm-dialog';
import PageContainer from '../../components/page-container';
import { requireRouteParam } from '@/lib/route-params';
import { translate } from '@/i18n';

export default function SettingsPage() {
  const { tenantId, projectId } = useParams<{ tenantId: string; projectId: string }>();
  const navigate = useNavigate();
  const { data: project, isLoading } = useProject(tenantId, projectId);
  const updateProject = useUpdateProject(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId')
  );
  const archiveProject = useArchiveProject(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId')
  );
  const restoreProject = useRestoreProject(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId')
  );
  const { data: apiKeys, isLoading: keysLoading } = useApiKeys(tenantId, projectId);
  const createApiKey = useCreateApiKey(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId')
  );

  const [name, setName] = useState('');
  const [projectSlug, setProjectSlug] = useState('');
  const [description, setDescription] = useState('');
  const [initialized, setInitialized] = useState(false);

  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [showArchiveDialog, setShowArchiveDialog] = useState(false);
  const [revokingKeyId, setRevokingKeyId] = useState<string | null>(null);

  if (!initialized && project) {
    setName(project.name);
    setProjectSlug(project.slug);
    setDescription(project.description || '');
    setInitialized(true);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const handleUpdateProject = async (e: FormEvent) => {
    e.preventDefault();
    await updateProject.mutateAsync({ name, slug: projectSlug, description });
  };

  const handleCreateKey = async (e: FormEvent) => {
    e.preventDefault();
    const result = await createApiKey.mutateAsync({ name: newKeyName });
    setCreatedKey(result.full_key || null);
    setNewKeyName('');
  };

  return (
    <PageContainer className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          {translate('projects:auto.project_settings')}
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {translate('projects:auto.configure_your_project_details_and_api_keys')}
        </p>
      </div>

      {/* General */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {translate('projects:auto.general')}
          </h2>
        </div>
        <form onSubmit={handleUpdateProject} className="space-y-4 p-6">
          {updateProject.isSuccess && (
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-400">
              {translate('projects:auto.project_updated_successfully')}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              {translate('projects:auto.name')}
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              {translate('projects:auto.slug')}
            </label>
            <input
              type="text"
              value={projectSlug}
              onChange={(e) => setProjectSlug(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              {translate('projects:auto.description')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={updateProject.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {updateProject.isPending
                ? translate('projects:auto.saving')
                : translate('projects:auto.save_changes')}
            </button>
          </div>
        </form>
      </div>

      {/* API Keys */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {translate('projects:auto.api_keys')}
          </h2>
        </div>

        <form
          onSubmit={handleCreateKey}
          className="border-b border-slate-200 px-6 py-4 dark:border-slate-700"
        >
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {translate('projects:auto.key_name')}
              </label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder={translate('projects:auto.e_g_ci_cd_pipeline')}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                required
              />
            </div>
            <button
              type="submit"
              disabled={createApiKey.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {translate('projects:auto.create_key')}
            </button>
          </div>
          {createdKey && (
            <div className="mt-3 rounded-md bg-green-50 p-3 dark:bg-green-900/30">
              <p className="text-sm font-medium text-green-800 dark:text-green-400">
                {translate('projects:auto.api_key_created_copy_it_now_it')}
              </p>
              <code className="mt-1 block break-all rounded bg-green-100 p-2 font-mono text-xs text-green-900 dark:bg-green-900/50 dark:text-green-300">
                {createdKey}
              </code>
            </div>
          )}
        </form>

        <div className="divide-y divide-slate-100 dark:divide-slate-700">
          {keysLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
            </div>
          ) : !apiKeys || apiKeys.length === 0 ? (
            <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
              {translate('projects:auto.no_api_keys_yet')}
            </div>
          ) : (
            apiKeys.map((key) => (
              <div key={key.id} className="flex items-center justify-between px-6 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {key.name}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {key.key_prefix}
                    {translate('projects:auto.created')} {formatDateOnly(key.created_at)}
                    {key.last_used_at && (
                      <>
                        {' | '}
                        {translate('projects:lastUsed', {
                          date: formatDateOnly(key.last_used_at),
                        })}
                      </>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {key.revoked_at && (
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {translate('projects:auto.revoked')}
                    </span>
                  )}
                  {!key.revoked_at && (
                    <button
                      onClick={() => setRevokingKeyId(key.id)}
                      className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    >
                      {translate('projects:auto.revoke')}
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Danger zone */}
      <div className="rounded-lg border border-red-200 bg-white shadow-sm dark:border-red-800 dark:bg-slate-800">
        <div className="border-b border-red-200 px-6 py-4 dark:border-red-800">
          <h2 className="text-lg font-semibold text-red-900 dark:text-red-400">
            {translate('projects:auto.danger_zone')}
          </h2>
        </div>
        <div className="p-6">
          {project?.is_archived ? (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {translate('projects:auto.restore_project')}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {translate('projects:auto.this_project_is_currently_archived')}
                </p>
              </div>
              <button
                onClick={() => restoreProject.mutate()}
                className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                {translate('projects:auto.restore')}
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {translate('projects:auto.archive_project')}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {translate('projects:auto.archived_projects_are_read_only_and_hidden')}
                </p>
              </div>
              <button
                onClick={() => setShowArchiveDialog(true)}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                {translate('projects:auto.archive')}
              </button>
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={showArchiveDialog}
        title={translate('projects:auto.archive_project')}
        message={translate('projects:auto.are_you_sure_you_want_to_archive_this_project_it_will_b')}
        variant="danger"
        confirmLabel={translate('projects:auto.archive')}
        onConfirm={async () => {
          await archiveProject.mutateAsync();
          setShowArchiveDialog(false);
          navigate(`/tenants/${tenantId}`);
        }}
        onCancel={() => setShowArchiveDialog(false)}
      />

      {revokingKeyId && (
        <RevokeKeyDialog
          tenantId={requireRouteParam(tenantId, 'tenantId')}
          projectId={requireRouteParam(projectId, 'projectId')}
          keyId={revokingKeyId}
          onClose={() => setRevokingKeyId(null)}
        />
      )}
    </PageContainer>
  );
}

function RevokeKeyDialog({
  tenantId,
  projectId,
  keyId,
  onClose,
}: {
  tenantId: string;
  projectId: string;
  keyId: string;
  onClose: () => void;
}) {
  const revokeApiKey = useRevokeApiKey(tenantId, projectId, keyId);

  return (
    <ConfirmDialog
      open
      title={translate('projects:auto.revoke_api_key')}
      message={translate('projects:auto.are_you_sure_you_want_to_revoke_this_api_key_this_actio')}
      variant="danger"
      confirmLabel={translate('projects:auto.revoke')}
      onConfirm={async () => {
        await revokeApiKey.mutateAsync();
        onClose();
      }}
      onCancel={onClose}
    />
  );
}
