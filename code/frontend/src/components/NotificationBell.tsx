import { useState, useRef, useEffect } from 'react';
import { useNotifications, useMarkRead, useMarkAllRead } from '../hooks/useNotifications';

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { data: notificationsData } = useNotifications({ page_size: 10 });
  const markAllRead = useMarkAllRead();

  const notifications = notificationsData?.items || [];
  const unreadCount = notifications.filter((n) => !n.read_at).length;

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
      >
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
          />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 w-80 rounded-md border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-slate-900">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllRead.mutate()}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {!notifications || notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-slate-500">
                No notifications
              </div>
            ) : (
              notifications.map((notif) => (
                <NotificationItem
                  key={notif.id}
                  notification={notif}
                  onClick={() => {
                    // TODO: Add navigation based on entity_type/entity_id
                    setOpen(false);
                  }}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function NotificationItem({
  notification,
  onClick,
}: {
  notification: { id: string; title: string; read_at: string | null; created_at: string };
  onClick: () => void;
}) {
  const markRead = useMarkRead(notification.id);

  return (
    <button
      onClick={() => {
        if (!notification.read_at) markRead.mutate();
        onClick();
      }}
      className={`flex w-full flex-col gap-1 px-4 py-3 text-left hover:bg-slate-50 ${
        !notification.read_at ? 'bg-blue-50/50' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm font-medium text-slate-900">
          {notification.title}
        </span>
        {!notification.read_at && (
          <span className="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500" />
        )}
      </div>
      <time className="text-xs text-slate-400">
        {new Date(notification.created_at).toLocaleDateString()}
      </time>
    </button>
  );
}
