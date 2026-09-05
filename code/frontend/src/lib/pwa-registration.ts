import { registerSW } from 'virtual:pwa-register';

export interface PwaRegistrationOptions {
  onNeedRefresh: (reload: () => void) => void;
  onOfflineReady?: () => void;
}

export function supportsServiceWorker(): boolean {
  return typeof navigator !== 'undefined' && 'serviceWorker' in navigator;
}

export function registerPwaServiceWorker({
  onNeedRefresh,
  onOfflineReady,
}: PwaRegistrationOptions) {
  if (!supportsServiceWorker()) return () => undefined;

  const updateServiceWorker = registerSW({
    immediate: true,
    onNeedRefresh() {
      onNeedRefresh(() => {
        void updateServiceWorker(true);
      });
    },
    onOfflineReady() {
      onOfflineReady?.();
    },
    onRegisterError(error) {
      if (import.meta.env.DEV) console.error('PWA service worker registration failed', error);
    },
  });

  return () => undefined;
}
