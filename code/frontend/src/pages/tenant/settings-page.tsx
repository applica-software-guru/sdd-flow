import { formatDateTime } from '@/lib/format';
import { useState, FormEvent } from 'react';
import { useParams } from 'react-router-dom';
import { useCurrentUser } from '../../hooks/use-auth';
import {
  useTenant,
  useUpdateTenant,
  useTenantInvitations,
  useTenantMembers,
  useInviteMember,
  useCancelInvitation,
  useRemoveMember,
} from '../../hooks/use-tenants';
import ConfirmDialog from '../../components/confirm-dialog';
import PageContainer from '../../components/page-container';
import { requireRouteParam } from '@/lib/route-params';
import { translate } from '@/i18n';

export default function SettingsPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const { data: currentUser } = useCurrentUser();
  const { data: tenant, isLoading } = useTenant(tenantId);
  const { data: invitations, isLoading: invitationsLoading } = useTenantInvitations(tenantId);
  const { data: members, isLoading: membersLoading } = useTenantMembers(tenantId);
  const updateTenant = useUpdateTenant(requireRouteParam(tenantId, 'tenantId'));
  const inviteMember = useInviteMember(requireRouteParam(tenantId, 'tenantId'));
  const cancelInvitation = useCancelInvitation(requireRouteParam(tenantId, 'tenantId'));
  const removeMember = useRemoveMember(requireRouteParam(tenantId, 'tenantId'));

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [nameInitialized, setNameInitialized] = useState(false);

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [cancellingInvitationId, setCancellingInvitationId] = useState<string | null>(null);
  const [removingMemberId, setRemovingMemberId] = useState<string | null>(null);

  if (!nameInitialized && tenant) {
    setName(tenant.name);
    setSlug(tenant.slug);
    setNameInitialized(true);
  }

  const myMember = members?.find((m) => m.user_id === currentUser?.id);
  const isAdmin = myMember?.role === 'owner' || myMember?.role === 'admin';

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

  const getStatusLabelClass = (status: 'pending' | 'accepted' | 'expired') => {
    if (status === 'accepted') {
      return 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300';
    }
    if (status === 'expired') {
      return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300';
    }
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300';
  };

  return (
    <PageContainer className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          {translate('tenants:auto.tenant_settings_2')}
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {isAdmin
            ? translate('tenants:auto.manage_your_tenant_configuration_and_members')
            : translate('tenants:auto.view_your_tenant_configuration')}
        </p>
      </div>

      {/* General settings */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {translate('tenants:auto.general')}
          </h2>
        </div>
        {isAdmin ? (
          <form onSubmit={handleUpdateTenant} className="space-y-4 p-6">
            {updateTenant.isSuccess && (
              <div className="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-400">
                {translate('tenants:auto.tenant_updated_successfully')}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {translate('tenants:auto.name')}
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
                {translate('tenants:auto.slug')}
              </label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={updateTenant.isPending}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {updateTenant.isPending
                  ? translate('tenants:auto.saving')
                  : translate('tenants:auto.save_changes')}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-4 p-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {translate('tenants:auto.name')}
              </label>
              <p className="mt-1 text-sm text-slate-900 dark:text-slate-100">{tenant?.name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {translate('tenants:auto.slug')}
              </label>
              <p className="mt-1 text-sm text-slate-900 dark:text-slate-100">{tenant?.slug}</p>
            </div>
          </div>
        )}
      </div>

      {/* Members — only visible to owner/admin */}
      {isAdmin && (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {translate('tenants:auto.members')}
            </h2>
          </div>

          {/* Invite form */}
          <form
            onSubmit={handleInvite}
            className="border-b border-slate-200 px-6 py-4 dark:border-slate-700"
          >
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  {translate('tenants:auto.invite_by_email')}
                </label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder={translate('tenants:auto.colleague_example_com')}
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  {translate('tenants:auto.role')}
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="sdd-select mt-1 block rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                >
                  <option value="viewer">{translate('tenants:auto.viewer')}</option>
                  <option value="member">{translate('tenants:auto.member')}</option>
                  <option value="admin">{translate('tenants:auto.admin')}</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={inviteMember.isPending}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {translate('tenants:auto.invite')}
              </button>
            </div>
            {inviteMember.isError && (
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">
                {translate('tenants:auto.failed_to_invite_member')}
              </p>
            )}
          </form>

          {/* Invitations list */}
          <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {translate('tenants:auto.invitations')}
            </h3>
            {invitationsLoading ? (
              <div className="mt-3 flex items-center justify-center py-4">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
              </div>
            ) : !invitations || invitations.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                {translate('tenants:auto.no_invitations_yet')}
              </p>
            ) : (
              <div className="mt-3 space-y-2">
                {invitations.map((invitation) => (
                  <div
                    key={invitation.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-slate-200 px-3 py-2 dark:border-slate-700"
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                        {invitation.email}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {translate('tenants:auto.role_2')} {invitation.role}{' '}
                        {translate('tenants:auto.sent')} {formatDateTime(invitation.created_at)}{' '}
                        {translate('tenants:auto.expires')} {formatDateTime(invitation.expires_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${getStatusLabelClass(invitation.status)}`}
                      >
                        {invitation.status}
                      </span>
                      {invitation.status === 'pending' && (
                        <button
                          onClick={() => setCancellingInvitationId(invitation.id)}
                          className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                        >
                          {translate('tenants:auto.cancel')}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Members list */}
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            {membersLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
              </div>
            ) : !members || members.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                {translate('tenants:auto.no_members_yet')}
              </div>
            ) : (
              members.map((member) => (
                <div key={member.id} className="flex items-center justify-between px-6 py-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
                      {member.display_name
                        ?.split(' ')
                        .map((n: string) => n[0])
                        .join('')
                        .toUpperCase() || '?'}
                    </div>
                    <div className="min-w-0">
                      <p
                        className="truncate text-sm font-medium text-slate-900 dark:text-slate-100"
                        title={member.email}
                      >
                        {member.display_name}
                      </p>
                      <p
                        className="truncate text-xs text-slate-500 dark:text-slate-400"
                        title={member.email}
                      >
                        {member.email}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium capitalize text-slate-600 dark:bg-slate-700 dark:text-slate-400">
                      {member.role}
                    </span>
                    {member.role !== 'owner' && (
                      <button
                        onClick={() => setRemovingMemberId(member.id)}
                        className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      >
                        {translate('tenants:auto.remove')}
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!cancellingInvitationId}
        title={translate('tenants:auto.cancel_invitation')}
        message={translate('tenants:auto.the_invitation_link_will_stop_working_immediately')}
        variant="danger"
        confirmLabel={translate('tenants:auto.cancel_invitation')}
        onConfirm={async () => {
          if (cancellingInvitationId) {
            await cancelInvitation.mutateAsync(cancellingInvitationId);
            setCancellingInvitationId(null);
          }
        }}
        onCancel={() => setCancellingInvitationId(null)}
      />

      <ConfirmDialog
        open={!!removingMemberId}
        title={translate('tenants:auto.remove_member')}
        message={translate('tenants:auto.are_you_sure_you_want_to_remove_this_member_from_the_te')}
        variant="danger"
        confirmLabel={translate('tenants:auto.remove')}
        onConfirm={async () => {
          if (removingMemberId) {
            await removeMember.mutateAsync(removingMemberId);
            setRemovingMemberId(null);
          }
        }}
        onCancel={() => setRemovingMemberId(null)}
      />
    </PageContainer>
  );
}
