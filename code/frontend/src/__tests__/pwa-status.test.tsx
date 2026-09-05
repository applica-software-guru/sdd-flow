// @vitest-environment jsdom
import { act, cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import PwaStatus from '@/components/pwa-status';

let registerOptions: { onNeedRefresh: (reload: () => void) => void } | undefined;
const reloadUpdate = vi.fn();

vi.mock('@/lib/pwa-registration', () => ({
  registerPwaServiceWorker: vi.fn((options: { onNeedRefresh: (reload: () => void) => void }) => {
    registerOptions = options;
    return () => undefined;
  }),
}));

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { value, configurable: true });
  window.dispatchEvent(new Event(value ? 'online' : 'offline'));
}

describe('PwaStatus', () => {
  beforeEach(() => {
    registerOptions = undefined;
    reloadUpdate.mockClear();
    setOnline(true);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('shows a translated offline notice when connectivity is lost', () => {
    render(<PwaStatus />);

    act(() => setOnline(false));

    expect(screen.getByRole('region', { name: 'Network status' })).toBeTruthy();
    expect(screen.getByText('You are offline')).toBeTruthy();
  });

  it('shows an update prompt and reloads only after the user chooses it', async () => {
    const user = userEvent.setup();
    render(<PwaStatus />);

    act(() => registerOptions?.onNeedRefresh(reloadUpdate));

    expect(screen.getByRole('region', { name: 'Application update' })).toBeTruthy();
    expect(reloadUpdate).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: 'Reload now' }));

    expect(reloadUpdate).toHaveBeenCalledOnce();
  });

  it('uses the browser install prompt only after beforeinstallprompt is available', async () => {
    const user = userEvent.setup();
    const prompt = vi.fn<() => Promise<void>>(() => Promise.resolve());
    render(<PwaStatus />);

    const event = new Event('beforeinstallprompt') as Event & {
      prompt: () => Promise<void>;
      userChoice: Promise<{ outcome: 'accepted' }>;
    };
    event.prompt = prompt;
    event.userChoice = Promise.resolve({ outcome: 'accepted' });

    void act(() => {
      window.dispatchEvent(event);
    });

    expect(screen.getByRole('region', { name: 'Install SDD Flow' })).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Install app' }));

    expect(prompt).toHaveBeenCalledOnce();
  });
});
