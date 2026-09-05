import { Download, RefreshCw, WifiOff, X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { useOnlineState } from '@/hooks/use-online-state';
import { registerPwaServiceWorker } from '@/lib/pwa-registration';
import { cn } from '@/lib/utils';

type PromptOutcome = 'accepted' | 'dismissed';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: PromptOutcome }>;
}

export default function PwaStatus() {
  const { t } = useTranslation('common');
  const isOnline = useOnlineState();
  const [reloadUpdate, setReloadUpdate] = useState<(() => void) | null>(null);
  const [updateDismissed, setUpdateDismissed] = useState(false);
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [installDismissed, setInstallDismissed] = useState(false);

  const handleNeedRefresh = useCallback((reload: () => void) => {
    setUpdateDismissed(false);
    setReloadUpdate(() => reload);
  }, []);

  useEffect(
    () => registerPwaServiceWorker({ onNeedRefresh: handleNeedRefresh }),
    [handleNeedRefresh]
  );

  useEffect(() => {
    const handleBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      setInstallDismissed(false);
      setInstallPrompt(event as BeforeInstallPromptEvent);
    };
    const handleAppInstalled = () => {
      setInstallPrompt(null);
      setInstallDismissed(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const canShowInstall = installPrompt && !installDismissed;
  const canShowUpdate = reloadUpdate && !updateDismissed;

  if (isOnline && !canShowUpdate && !canShowInstall) return null;

  async function installApp() {
    if (!installPrompt) return;
    await installPrompt.prompt();
    const choice = await installPrompt.userChoice;
    if (choice.outcome === 'accepted' || choice.outcome === 'dismissed') {
      setInstallPrompt(null);
      setInstallDismissed(true);
    }
  }

  return (
    <div
      className="fixed inset-x-4 bottom-4 z-50 flex flex-col gap-2 sm:left-auto sm:max-w-md"
      aria-live="polite"
      aria-relevant="additions text"
    >
      {!isOnline ? (
        <section
          className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-950 shadow-lg dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100"
          aria-label={t('pwa.offlineLabel')}
        >
          <div className="flex items-start gap-3">
            <WifiOff className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <div>
              <p className="text-sm font-semibold">{t('pwa.offlineTitle')}</p>
              <p className="mt-1 text-sm">{t('pwa.offlineDescription')}</p>
            </div>
          </div>
        </section>
      ) : null}

      {canShowUpdate ? (
        <section
          className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-blue-950 shadow-lg dark:border-blue-900 dark:bg-blue-950 dark:text-blue-100"
          aria-label={t('pwa.updateLabel')}
        >
          <div className="flex items-start gap-3">
            <RefreshCw className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">{t('pwa.updateTitle')}</p>
              <p className="mt-1 text-sm">{t('pwa.updateDescription')}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" onClick={() => reloadUpdate()}>
                  {t('pwa.reload')}
                </Button>
                <Button size="sm" variant="outline" onClick={() => setUpdateDismissed(true)}>
                  {t('pwa.later')}
                </Button>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {canShowInstall ? (
        <section
          className={cn(
            'rounded-lg border border-border bg-background p-4 text-foreground shadow-lg',
            'dark:border-slate-700 dark:bg-slate-950'
          )}
          aria-label={t('pwa.installLabel')}
        >
          <div className="flex items-start gap-3">
            <Download className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">{t('pwa.installTitle')}</p>
              <p className="mt-1 text-sm text-muted-foreground">{t('pwa.installDescription')}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" onClick={installApp}>
                  {t('pwa.install')}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setInstallDismissed(true)}>
                  {t('pwa.notNow')}
                </Button>
              </div>
            </div>
            <Button
              type="button"
              size="icon"
              variant="ghost"
              className="h-8 w-8 shrink-0"
              onClick={() => setInstallDismissed(true)}
              aria-label={t('pwa.dismissInstall')}
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
