import { Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useMarkAllRead, useMarkRead, useNotifications } from '@/hooks/use-notifications';
import { formatDateOnly } from '@/lib/format';
import { cn } from '@/lib/utils';
import { translate } from '@/i18n';

export default function NotificationBell() {
  const { data } = useNotifications({ page_size: 10 });
  const markAllRead = useMarkAllRead();
  const notifications = data?.items ?? [];
  const unreadCount = notifications.filter((notification) => !notification.read_at).length;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={translate('notifications:unread', { count: unreadCount })}
        >
          <Bell aria-hidden="true" />
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-0.5 text-[10px] font-bold text-destructive-foreground">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0">
        <DropdownMenuLabel className="flex items-center justify-between px-4 py-3">
          <span>{translate('notifications:auto.notifications')}</span>
          {unreadCount > 0 && (
            <Button
              variant="link"
              size="sm"
              className="h-auto p-0 text-xs"
              onClick={() => markAllRead.mutate()}
            >
              {translate('notifications:auto.mark_all_read')}
            </Button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="m-0" />
        <div className="max-h-80 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              {translate('notifications:auto.no_notifications')}
            </div>
          ) : (
            notifications.map((notification) => (
              <NotificationItem key={notification.id} notification={notification} />
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function NotificationItem({
  notification,
}: {
  notification: { id: string; title: string; read_at: string | null; created_at: string };
}) {
  const markRead = useMarkRead(notification.id);
  return (
    <DropdownMenuItem
      onSelect={() => {
        if (!notification.read_at) markRead.mutate();
      }}
      className={cn(
        'flex cursor-pointer flex-col items-stretch gap-1 rounded-none px-4 py-3',
        !notification.read_at && 'bg-primary/5'
      )}
    >
      <span className="flex items-start justify-between gap-2">
        <span className="text-sm font-medium">{notification.title}</span>
        {!notification.read_at && (
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" aria-hidden="true" />
        )}
      </span>
      <time className="text-xs text-muted-foreground">
        {formatDateOnly(notification.created_at)}
      </time>
    </DropdownMenuItem>
  );
}
