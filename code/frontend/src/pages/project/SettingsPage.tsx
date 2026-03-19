import { useState, FormEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProject, useUpdateProject, useArchiveProject, useRestoreProject } from '../../hooks/useProjects';
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from '../../hooks/useApiKeys';
import ConfirmDialog from '../../components/ConfirmDialog';

export default function SettingsPage() {
  const { tenantId, projectId } = useParams<{ tenantId: string; projectId: string }>();
  const navigate = useNavigate();
  const { data: project, isLoading } = useProject(tenantId, projectId);
  const updateProject = useUpdateProject(tenantId!, projectId!);
  const archiveProject = useArchiveProject(tenantId!, projectId!);
  const restoreProject = useRestoreProject(tenantId!, projectId!);
  const { data: apiKeys, isLoading: keysLoading } = useApiKeys(tenantId, projectId);
  const createApiKey = useCreateApiKey(tenantId!, projectId!);

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
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Project Settings</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Configure your project details and API keys
        </p>
      </div>

      {/* General */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">General</h2>
        </div>
        <form onSubmit={handleUpdateProject} className="space-y-4 p-6">
          {updateProject.isSuccess && (
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-400">
              Project updated successfully
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Slug</label>
            <input
              type="text"
              value={projectSlug}
              onChange={(e) => setProjectSlug(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={updateProject.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {updateProject.isPending ? 'Saving...' : 'Save changes'}
            </button>
          </div>
        </form>
      </div>

      {/* API Keys */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">API Keys</h2>
        </div>

        <form onSubmit={handleCreateKey} className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Key name
              </label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., CI/CD Pipeline"
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
                required
              />
            </div>
            <button
              type="submit"
              disabled={createApiKey.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Create key
            </button>
          </div>
          {createdKey && (
            <div className="mt-3 rounded-md bg-green-50 p-3 dark:bg-green-900/30">
              <p className="text-sm font-medium text-green-800 dark:text-green-400">
                API key created! Copy it now -- it will not be shown again.
              </p>
              <code className="mt-1 block break-all rounded bg-green-100 p-2 text-xs font-mono text-green-900 dark:bg-green-900/50 dark:text-green-300">
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
              No API keys yet
            </div>
          ) : (
            apiKeys.map((key) => (
              <div key={key.id} className="flex items-center justify-between px-6 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{key.name}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {key.key_prefix}... | Created{' '}
                    {new Date(key.created_at).toLocaleDateString()}
                    {key.last_used_at &&
                      ` | Last used ${new Date(key.last_used_at).toLocaleDateString()}`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {key.revoked_at && (
                    <span className="text-xs text-slate-500 dark:text-slate-400">Revoked</span>
                  )}
                  {!key.revoked_at && (
                    <button
                      onClick={() => setRevokingKeyId(key.id)}
                      className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    >
                      Revoke
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
          <h2 className="text-lg font-semibold text-red-900 dark:text-red-400">Danger Zone</h2>
        </div>
        <div className="p-6">
          {project?.is_archived ? (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  Restore project
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  This project is currently archived
                </p>
              </div>
              <button
                onClick={() => restoreProject.mutate()}
                className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                Restore
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  Archive project
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Archived projects are read-only and hidden from the dashboard
                </p>
              </div>
              <button
                onClick={() => setShowArchiveDialog(true)}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Archive
              </button>
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={showArchiveDialog}
        title="Archive project"
        message="Are you sure you want to archive this project? It will become read-only."
        variant="danger"
        confirmLabel="Archive"
        onConfirm={async () => {
          await archiveProject.mutateAsync();
          setShowArchiveDialog(false);
          navigate(`/tenants/${tenantId}`);
        }}
        onCancel={() => setShowArchiveDialog(false)}
      />

      {revokingKeyId && (
        <RevokeKeyDialog
          tenantId={tenantId!}
          projectId={projectId!}
          keyId={revokingKeyId}
          onClose={() => setRevokingKeyId(null)}
        />
      )}
    </div>
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
      title="Revoke API key"
      message="Are you sure you want to revoke this API key? This action cannot be undone."
      variant="danger"
      confirmLabel="Revoke"
      onConfirm={async () => {
        await revokeApiKey.mutateAsync();
        onClose();
      }}
      onCancel={onClose}
    />
  );
}
