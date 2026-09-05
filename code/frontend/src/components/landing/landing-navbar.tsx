import { Menu, X } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import ThemeToggle from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';
import { useCurrentUser } from '@/hooks/use-auth';
import LandingContainer from './landing-container';

const navLinks = [
  { label: 'Features', href: '#features' },
  { label: 'How it Works', href: '#how-it-works' },
  { label: 'For Teams', href: '#for-teams' },
  { label: 'Open Source', href: '#open-source' },
];

export default function LandingNavbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data: user, isLoading } = useCurrentUser();
  return (
    <header className="sticky top-0 z-50 border-b bg-background/85 backdrop-blur-lg">
      <LandingContainer className="flex h-14 items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
            S
          </span>
          <span className="text-lg font-bold">SDD Flow</span>
        </Link>
        <nav className="hidden items-center gap-1 md:flex" aria-label="Landing page">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <div className="hidden w-44 items-center justify-end gap-1 sm:flex">
            <SessionActions user={Boolean(user)} loading={isLoading} />
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileOpen((open) => !open)}
            aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'}
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
          </Button>
        </div>
      </LandingContainer>
      {mobileOpen && (
        <div className="border-t bg-background md:hidden">
          <LandingContainer className="flex flex-col gap-1 py-3">
            <nav className="flex flex-col gap-1" aria-label="Mobile landing page">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                >
                  {link.label}
                </a>
              ))}
            </nav>
            <div className="my-2 border-t" />
            <div className="flex flex-col gap-2">
              <SessionActions
                user={Boolean(user)}
                loading={isLoading}
                mobile
                onNavigate={() => setMobileOpen(false)}
              />
            </div>
          </LandingContainer>
        </div>
      )}
    </header>
  );
}

function SessionActions({
  user,
  loading,
  mobile,
  onNavigate,
}: {
  user: boolean;
  loading: boolean;
  mobile?: boolean;
  onNavigate?: () => void;
}) {
  if (loading)
    return (
      <div
        role="status"
        aria-label="Checking session"
        className="h-9 w-28 animate-pulse rounded-lg bg-muted"
      />
    );
  if (user)
    return (
      <Button asChild className={mobile ? 'w-full' : undefined}>
        <Link to="/tenants" onClick={onNavigate}>
          Open app
        </Link>
      </Button>
    );
  return (
    <>
      <Button asChild variant="ghost" className={mobile ? 'w-full' : undefined}>
        <Link to="/login" onClick={onNavigate}>
          Log in
        </Link>
      </Button>
      <Button asChild className={mobile ? 'w-full' : undefined}>
        <Link to="/register" onClick={onNavigate}>
          Sign Up
        </Link>
      </Button>
    </>
  );
}
