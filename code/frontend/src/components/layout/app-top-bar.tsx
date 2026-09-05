import { Menu, Search } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '@/components/language-selector';
import NotificationBell from '@/components/notification-bell';
import WorkspaceSwitcher from '@/components/workspace-switcher';
import ThemeToggle from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';
import type { User } from '@/types';
import UserMenu from './user-menu';

export default function AppTopBar({
  user,
  onOpenNavigation,
}: {
  user?: User;
  onOpenNavigation: () => void;
}) {
  const { t } = useTranslation(['common', 'navigation']);
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b bg-card px-4">
      <div className="flex min-w-0 items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onOpenNavigation}
          aria-label={t('navigation:open')}
        >
          <Menu aria-hidden="true" />
        </Button>
        <NavLink to="/tenants" className="flex shrink-0 items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
            S
          </span>
          <span className="hidden text-lg font-bold sm:inline">SDD Flow</span>
        </NavLink>
        <div className="hidden sm:block">
          <WorkspaceSwitcher />
        </div>
      </div>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          className="hidden text-muted-foreground sm:flex"
          onClick={() =>
            document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))
          }
        >
          <Search aria-hidden="true" />
          {t('common:actions.search')}{' '}
          <kbd className="rounded bg-muted px-1.5 py-0.5 text-xs">⌘K</kbd>
        </Button>
        <LanguageSelector />
        <ThemeToggle />
        <NotificationBell />
        <UserMenu user={user} />
      </div>
    </header>
  );
}
