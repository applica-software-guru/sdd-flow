import { useSyncExternalStore } from 'react';

function getOnlineSnapshot() {
  if (typeof navigator === 'undefined') return true;
  return navigator.onLine;
}

function subscribeToOnlineState(callback: () => void) {
  if (typeof window === 'undefined') return () => undefined;
  window.addEventListener('online', callback);
  window.addEventListener('offline', callback);
  return () => {
    window.removeEventListener('online', callback);
    window.removeEventListener('offline', callback);
  };
}

export function useOnlineState() {
  return useSyncExternalStore(subscribeToOnlineState, getOnlineSnapshot, () => true);
}
