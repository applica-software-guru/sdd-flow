import PageContainer from '../../components/PageContainer';
import {
  useNotificationPreferences,
  useUpdateNotificationPreference,
} from '../../hooks/useNotifications';

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

export default function NotificationPreferencesPage() {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updatePreference = useUpdateNotificationPreference();

  return (
    <PageContainer className="py-8">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
        Notification preferences
      </h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
        Choose which events send you an email. In-app notifications are always on.
      </p>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : (
        <ul className="mt-6 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white shadow-sm dark:divide-slate-700 dark:border-slate-700 dark:bg-slate-800">
          {preferences?.map((pref) => {
            const meta = EVENT_LABELS[pref.event_type] ?? {
              title: pref.event_type,
              description: '',
            };
            return (
              <li
                key={pref.event_type}
                className="flex items-start justify-between gap-4 px-6 py-4"
              >
                <div>
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
    </PageContainer>
  );
}
