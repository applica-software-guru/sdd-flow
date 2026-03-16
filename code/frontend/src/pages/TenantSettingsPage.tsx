import { useState, FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import {
  useTenant,
  useUpdateTenant,
  useTenantMembers,
  useInviteMember,
  useRemoveMember,
} from '../hooks/useTenants';
import ConfirmDialog from '../components/ConfirmDialog';

export default function TenantSettingsPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const { data: tenant, isLoading } = useTenant(tenantId);
  const { data: members, isLoading: membersLoading } = useTenantMembers(tenantId);
  const updateTenant = useUpdateTenant(tenantId!);
  const inviteMember = useInviteMember(tenantId!);
  const removeMember = useRemoveMember(tenantId!);

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [nameInitialized, setNameInitialized] = useState(false);

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [removingMemberId, setRemovingMemberId] = useState<string | null>(null);

  if (!nameInitialized && tenant) {
    setName(tenant.name);
    setSlug(tenant.slug);
    setNameInitialized(true);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const handleUpdateTenant = async (e: FormEvent) => {
    e.preventDefault();
    await updateTenant.mutateAsync({ name, slug });
  };

  const handleInvite = async (e: FormEvent) => {
    e.preventDefault();
    await inviteMember.mutateAsync({ email: inviteEmail, role: inviteRole });
    setInviteEmail('');
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Tenant Settings</h1>
        <p className="mt-1 text-sm text-slate-500">
          Manage your tenant configuration and members
        </p>
      </div>

      {/* General settings */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-slate-900">General</h2>
        </div>
        <form onSubmit={handleUpdateTenant} className="space-y-4 p-6">
          {updateTenant.isSuccess && (
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-700">
              Tenant updated successfully
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Slug
            </label>
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={updateTenant.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {updateTenant.isPending ? 'Saving...' : 'Save changes'}
            </button>
          </div>
        </form>
      </div>

      {/* Members */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-slate-900">Members</h2>
        </div>

        {/* Invite form */}
        <form onSubmit={handleInvite} className="border-b border-slate-200 px-6 py-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium text-slate-700">
                Invite by email
              </label>
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@example.com"
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Role
              </label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="mt-1 block rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="viewer">Viewer</option>
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={inviteMember.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Invite
            </button>
          </div>
          {inviteMember.isError && (
            <p className="mt-2 text-sm text-red-600">
              Failed to invite member
            </p>
          )}
        </form>

        {/* Members list */}
        <div className="divide-y divide-slate-100">
          {membersLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
            </div>
          ) : !members || members.length === 0 ? (
            <div className="px-6 py-8 text-center text-sm text-slate-500">
              No members yet
            </div>
          ) : (
            members.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between px-6 py-3"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700">
                    {member.display_name
                      ?.split(' ')
                      .map((n: string) => n[0])
                      .join('')
                      .toUpperCase() || '?'}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {member.display_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {member.email}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium capitalize text-slate-600">
                    {member.role}
                  </span>
                  {member.role !== 'owner' && (
                    <button
                      onClick={() => setRemovingMemberId(member.id)}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <ConfirmDialog
        open={!!removingMemberId}
        title="Remove member"
        message="Are you sure you want to remove this member from the tenant?"
        variant="danger"
        confirmLabel="Remove"
        onConfirm={async () => {
          if (removingMemberId) {
            await removeMember.mutateAsync(removingMemberId);
            setRemovingMemberId(null);
          }
        }}
        onCancel={() => setRemovingMemberId(null)}
      />
    </div>
  );
}
