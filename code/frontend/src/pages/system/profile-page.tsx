import { useState, type FormEvent, type ReactNode } from 'react';
import PageContainer from '../../components/page-container';
import { useCurrentUser, useUpdateProfile, useChangePassword } from '../../hooks/use-auth';
import {
  useNotificationPreferences,
  useUpdateNotificationPreference,
} from '../../hooks/use-notifications';
import { useToast } from '../../context/toast';
import { initialsOf } from '../../utils/user';

const EVENT_LABELS: Record<string, { title: string; description: string }> = {
  comment_added: {
    title: 'New comments',
    description:
      'Someone comments on a CR or bug you are involved in (author, assignee, or previous commenter). Enabled by default.',
  },
  content_changed: {
    title: 'Content changes',
    description:
      'The title or body of a CR or bug you are involved in is modified. Disabled by default — opt in here.',
  },
  assigned: {
    title: 'Assigned to you',
    description: 'A CR or bug is assigned to you.',
  },
  status_changed: {
    title: 'Status changes',
    description: 'A CR or bug you created or are assigned to changes status.',
  },
  mentioned: {
    title: 'Mentions',
    description: 'Someone mentions you in a comment (@username).',
  },
};

function Spinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
    </div>
  );
}

function Card({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="mt-8 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="border-b border-slate-100 px-6 py-4 dark:border-slate-700">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
        {description && (
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{description}</p>
        )}
      </div>
      <div className="px-6 py-4">{children}</div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Account section
// ---------------------------------------------------------------------------

function AccountSection() {
  const { data: user } = useCurrentUser();
  const updateProfile = useUpdateProfile();
  const { addToast } = useToast();
  const [name, setName] = useState<string | null>(null);
  const displayName = name ?? user?.display_name ?? '';
  const dirty = name !== null && name !== (user?.display_name ?? '');

  const handleSave = async () => {
    try {
      await updateProfile.mutateAsync({ display_name: displayName.trim() });
      setName(null);
      addToast('Profile updated', 'success');
    } catch (err) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        'Failed to update profile';
      addToast(detail, 'error');
    }
  };

  return (
    <Card title="Account" description="Your public identity across the platform.">
      <div className="flex items-center gap-4">
        {user?.avatar_url ? (
          <img
            src={user.avatar_url}
            alt=""
            className="h-12 w-12 shrink-0 rounded-full object-cover"
          />
        ) : (
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
            {initialsOf(user?.display_name)}
          </div>
        )}
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span
              className="truncate text-sm font-medium text-slate-900 dark:text-slate-100"
              title={user?.email}
            >
              {user?.email}
            </span>
            {user?.email_verified && (
              <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                verified
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Email cannot be changed.</p>
        </div>
      </div>

      <div className="mt-6 max-w-md">
        <label
          htmlFor="display-name"
          className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400"
        >
          Display name
        </label>
        <div className="mt-2 flex gap-2">
          <input
            id="display-name"
            type="text"
            value={displayName}
            maxLength={80}
            onChange={(e) => setName(e.target.value)}
            className="min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          />
          <button
            onClick={handleSave}
            disabled={!dirty || updateProfile.isPending || !displayName.trim()}
            className="shrink-0 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {updateProfile.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Security section
// ---------------------------------------------------------------------------

function GoogleBadge({ small = false }: { small?: boolean }) {
  return (
    <span
      className={`flex ${small ? 'h-6 w-6' : 'h-10 w-10'} shrink-0 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-slate-200 dark:bg-slate-700 dark:ring-slate-600`}
    >
      <svg className={small ? 'h-3.5 w-3.5' : 'h-5 w-5'} viewBox="0 0 48 48" aria-hidden="true">
        <path
          fill="#EA4335"
          d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 9.08 30.47 7 24 9.5 12.67 2.5 2 12.17 2 24c0 2.25.39 4.44.65 6.61z"
        />
        <path
          fill="#4285F4"
          d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
        />
        <path
          fill="#FBBC05"
          d="M10.53 28.59A14.5 14.5 0 019.5 24c0-1.56.27-3.07.77-4.49L2.65 13.4A23.94 23.94 0 001 24c0 3.88.93 7.54 2.56 10.6l6.97-6z"
        />
        <path
          fill="#34A853"
          d="M24 46c5.94 0 10.92-1.96 14.56-5.32l-7.09-5.49C29.58 36.4 26.99 37.5 24 37.5c-5.27 0-9.75-3.43-11.34-8.2l-7.2 5.57C9.21 40.41 16.03 45.5 24 45.5z"
        />
      </svg>
    </span>
  );
}

function SecuritySection() {
  const { data: user } = useCurrentUser();
  const changePassword = useChangePassword();
  const { addToast } = useToast();

  const hasPassword = user?.has_password ?? false;
  const googleOnly = !hasPassword && (user?.google_linked ?? false);
  const [showSetPassword, setShowSetPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const inputClass =
    'mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (hasPassword && !currentPassword) {
      setError('Current password is required');
      return;
    }
    try {
      await changePassword.mutateAsync({
        current_password: hasPassword ? currentPassword : undefined,
        new_password: newPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setError('');
      setShowSetPassword(false);
      addToast(
        hasPassword
          ? 'Password updated — other sessions have been signed out'
          : 'Password set — you can now sign in with email and password',
        'success'
      );
    } catch (err) {
      const detail =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        'Failed to change password';
      setError(detail);
    }
  };

  // Google-only account: replace the password-change form with an info panel
  // explaining the sign-in method (optionally still allow setting a password
  // for hybrid login, per CR-035).
  if (googleOnly && !showSetPassword) {
    return (
      <Card title="Security" description="How you sign in to SDD Flow.">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 items-center gap-4">
            <GoogleBadge />
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                You sign in with Google
              </p>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Your account {user?.email} is managed by Google — there is no password to change
                here.
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowSetPassword(true)}
            className="shrink-0 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
          >
            Set a password
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card
      title="Security"
      description={
        googleOnly
          ? 'Set a password to also sign in with your email and password, in addition to Google.'
          : hasPassword
            ? 'Change your password. Other sessions are signed out after the change.'
            : 'Set a password to sign in with your email.'
      }
    >
      {googleOnly && (
        <div className="mb-4 flex items-center gap-3 rounded-md bg-blue-50 px-4 py-3 dark:bg-blue-900/30">
          <GoogleBadge small />
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Optional — you can keep signing in with Google as before.
          </p>
          <button
            onClick={() => setShowSetPassword(false)}
            className="ml-auto shrink-0 text-xs font-medium text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
          >
            Cancel
          </button>
        </div>
      )}
      <form onSubmit={handleSubmit} className="max-w-md">
        {hasPassword && (
          <div>
            <label
              htmlFor="current-password"
              className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400"
            >
              Current password
            </label>
            <input
              id="current-password"
              type="password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className={inputClass}
            />
          </div>
        )}
        <div className={hasPassword ? 'mt-4' : ''}>
          <label
            htmlFor="new-password"
            className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400"
          >
            {hasPassword ? 'New password' : 'New password'}
          </label>
          <input
            id="new-password"
            type="password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className={inputClass}
          />
        </div>
        <div className="mt-4">
          <label
            htmlFor="confirm-password"
            className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400"
          >
            Confirm new password
          </label>
          <input
            id="confirm-password"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className={inputClass}
          />
        </div>
        {error && (
          <p className="mt-3 text-sm text-red-600 dark:text-red-400" role="alert">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={changePassword.isPending}
          className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {changePassword.isPending ? 'Saving…' : hasPassword ? 'Change password' : 'Set password'}
        </button>
      </form>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Notification preferences section (relocated from the old settings page)
// ---------------------------------------------------------------------------

function NotificationPreferencesSection() {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updatePreference = useUpdateNotificationPreference();

  return (
    <Card
      title="Notification preferences"
      description="Choose which events send you an email. In-app notifications are always on."
    >
      {isLoading ? (
        <Spinner />
      ) : (
        <ul className="divide-y divide-slate-200 dark:divide-slate-700">
          {preferences?.map((pref) => {
            const meta = EVENT_LABELS[pref.event_type] ?? {
              title: pref.event_type,
              description: '',
            };
            return (
              <li
                key={pref.event_type}
                className="flex items-start justify-between gap-4 py-4 first:pt-0 last:pb-0"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {meta.title}
                  </p>
                  {meta.description && (
                    <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                      {meta.description}
                    </p>
                  )}
                </div>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    className="peer sr-only"
                    checked={pref.email_enabled}
                    disabled={updatePreference.isPending}
                    onChange={(e) =>
                      updatePreference.mutate({
                        event_type: pref.event_type,
                        email_enabled: e.target.checked,
                      })
                    }
                  />
                  <div className="peer h-6 w-11 rounded-full bg-slate-200 after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:shadow after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-5 dark:bg-slate-600 dark:peer-checked:bg-blue-500"></div>
                </label>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ProfilePage() {
  const { isLoading } = useCurrentUser();

  return (
    <PageContainer className="py-8">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Profile</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        Manage your account, security, and notification preferences.
      </p>

      {isLoading ? (
        <Spinner />
      ) : (
        <div className="mt-2">
          <AccountSection />
          <SecuritySection />
          <div id="notifications">
            <NotificationPreferencesSection />
          </div>
        </div>
      )}
    </PageContainer>
  );
}
