import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import UserName from '../components/user-name';
import { initialsOf } from '../utils/user';
import UserCell from '../components/user-cell';
import ProfilePage from '../pages/system/profile-page';
import { ToastProvider } from '../context/toast-context';
import type { NotificationPreference } from '../hooks/use-notifications';
import type { User } from '../types';

describe('UserName', () => {
  it('renders initials avatar and truncated name with email tooltip', () => {
    const markup = renderToStaticMarkup(<UserName name="Jane Doe" email="jane@example.com" />);
    expect(markup).toContain('>JD<');
    expect(markup).toContain('Jane Doe');
    // CR-035: email is only a tooltip, min-w-0 + truncate prevent overflow
    expect(markup).toContain('min-w-0');
    expect(markup).toContain('truncate');
    expect(markup).toContain('title="jane@example.com"');
    expect(markup).not.toContain('>jane@example.com<');
  });

  it('avatar keeps shrink-0 so the text can shrink instead of pushing siblings', () => {
    const markup = renderToStaticMarkup(<UserName name="Jane Doe" email="jane@example.com" />);
    expect(markup).toContain('shrink-0');
  });

  it('falls back to email as visible text only when there is no name', () => {
    const markup = renderToStaticMarkup(<UserName name={null} email="long.name@example.com" />);
    expect(markup).toContain('long.name@example.com');
    expect(markup).toContain('truncate');
  });

  it('renders the fallback (with ? avatar) when neither name nor email exist', () => {
    const markup = renderToStaticMarkup(<UserName name={null} email={null} fallback="Unknown" />);
    expect(markup).toContain('>?<');
    expect(markup).toContain('Unknown');
  });

  it('renders a plain fallback span when the avatar is hidden', () => {
    const markup = renderToStaticMarkup(
      <UserName name={null} email={null} fallback="--" showAvatar={false} />
    );
    expect(markup).toContain('--');
    expect(markup).not.toContain('shrink-0');
  });
});

describe('initialsOf', () => {
  it('returns initials for multi-word names', () => {
    expect(initialsOf('Jane Doe')).toBe('JD');
  });

  it('returns ? for empty/missing names', () => {
    expect(initialsOf(null)).toBe('?');
    expect(initialsOf('')).toBe('?');
  });
});

describe('UserCell', () => {
  it('keeps the em-dash placeholder when there is no user', () => {
    const markup = renderToStaticMarkup(<UserCell user={null} />);
    expect(markup).toContain('--');
  });

  it('renders the shared UserName pattern for a user', () => {
    const user = { id: 'u1', display_name: 'Jane Doe', email: 'jane@example.com' };
    const markup = renderToStaticMarkup(<UserCell user={user} />);
    expect(markup).toContain('Jane Doe');
    expect(markup).toContain('truncate');
  });
});

describe('ProfilePage', () => {
  const mockUser: User = {
    id: 'u1',
    email: 'jane@example.com',
    display_name: 'Jane Doe',
    email_verified: true,
    platform_role: 'user',
    has_password: true,
    google_linked: false,
    created_at: '2026-09-04T00:00:00Z',
  };

  const mockPrefs: NotificationPreference[] = [
    { event_type: 'comment_added', email_enabled: true },
    { event_type: 'content_changed', email_enabled: false },
    { event_type: 'assigned', email_enabled: false },
  ];

  function renderPage(user: User) {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    client.setQueryData(['auth', 'me'], user);
    client.setQueryData(['notification-preferences'], mockPrefs);
    return renderToStaticMarkup(
      <QueryClientProvider client={client}>
        <ToastProvider>
          <ProfilePage />
        </ToastProvider>
      </QueryClientProvider>
    );
  }

  it('renders the unified Profile page with account, security and notification sections', () => {
    const markup = renderPage(mockUser);
    expect(markup).toContain('Profile');
    expect(markup).toContain('Account');
    expect(markup).toContain('Security');
    expect(markup).toContain('Notification preferences');
  });

  it('shows email as read-only with verified badge and editable display name', () => {
    const markup = renderPage(mockUser);
    expect(markup).toContain('jane@example.com');
    expect(markup).toContain('verified');
    expect(markup).toContain('Email cannot be changed.');
    expect(markup).toContain('Display name');
  });

  it('asks for the current password when the account has one', () => {
    const markup = renderPage(mockUser);
    expect(markup).toContain('Current password');
    expect(markup).toContain('Change password');
  });

  it('shows a Google sign-in info panel instead of the password form for Google-only accounts', () => {
    const googleOnly: User = { ...mockUser, has_password: false, google_linked: true };
    const markup = renderPage(googleOnly);
    expect(markup).toContain('You sign in with Google');
    expect(markup).not.toContain('Current password');
    expect(markup).not.toContain('New password');
    // Optional hybrid login still available (CR-035)
    expect(markup).toContain('Set a password');
  });

  it('offers setting an initial password for accounts without one', () => {
    const noPassword: User = { ...mockUser, has_password: false, google_linked: true };
    const markup = renderPage(noPassword);
    // The Set-password form is not shown until the user asks for it
    expect(markup).not.toContain('Confirm new password');
  });

  it('renders the relocated notification preferences toggles', () => {
    const markup = renderPage(mockUser);
    expect(markup).toContain('New comments');
    expect(markup).toContain('Content changes');
    expect(markup).toContain('In-app notifications are always on');
  });
});
