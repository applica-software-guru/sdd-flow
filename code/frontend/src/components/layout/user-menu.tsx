import { LogOut, UserRound } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useLogout } from '@/hooks/use-auth';
import type { User } from '@/types';
import { initialsOf } from '@/utils/user';

export default function UserMenu({ user }: { user?: User }) {
  const logout = useLogout();
  const navigate = useNavigate();
  const { t } = useTranslation(['common', 'navigation']);

  async function handleLogout() {
    await logout.mutateAsync();
    navigate('/login');
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label={t('navigation:openUserMenu')}>
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
            {initialsOf(user?.display_name)}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="min-w-0">
          <p className="truncate font-medium" title={user?.display_name}>
            {user?.display_name}
          </p>
          <p className="truncate text-xs font-normal text-muted-foreground" title={user?.email}>
            {user?.email}
          </p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => navigate('/settings/profile')}>
          <UserRound aria-hidden="true" />
          {t('navigation:profile')}
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-destructive focus:text-destructive"
          onSelect={() => void handleLogout()}
        >
          <LogOut aria-hidden="true" />
          {t('common:actions.signOut')}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
