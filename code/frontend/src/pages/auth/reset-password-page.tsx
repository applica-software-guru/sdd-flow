import { FormEvent, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '@/components/language-selector';
import { useResetPassword } from '../../hooks/use-auth';
import { getApiErrorMessage } from '../../api/errors';

export default function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();
  const resetPassword = useResetPassword();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationError, setValidationError] = useState('');
  const [success, setSuccess] = useState(false);
  const { t } = useTranslation('auth');

  const canSubmit = useMemo(
    () => !!token && newPassword.length >= 8 && confirmPassword.length >= 8,
    [token, newPassword, confirmPassword]
  );

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setValidationError('');

    if (!token) {
      setValidationError(t('validation.missingToken'));
      return;
    }
    if (newPassword !== confirmPassword) {
      setValidationError(t('validation.passwordMismatch'));
      return;
    }
    if (newPassword.length < 8) {
      setValidationError(t('validation.passwordLength'));
      return;
    }

    try {
      await resetPassword.mutateAsync({ token, new_password: newPassword });
      setSuccess(true);
    } catch {
      // handled by mutation state
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="absolute right-4 top-4">
        <LanguageSelector />
      </div>
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {t('reset.title')}
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{t('reset.subtitle')}</p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          {success ? (
            <div className="space-y-3">
              <div className="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-400">
                {t('reset.success')}
              </div>
              <Link
                to="/login"
                className="inline-flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                {t('reset.goToLogin')}
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {(validationError || resetPassword.isError) && (
                <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400">
                  {validationError || getApiErrorMessage(resetPassword.error, t('reset.failed'))}
                </div>
              )}

              <div>
                <label
                  htmlFor="newPassword"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300"
                >
                  {t('reset.newPassword')}
                </label>
                <input
                  id="newPassword"
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={t('minimumPassword')}
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm placeholder-slate-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                />
              </div>

              <div>
                <label
                  htmlFor="confirmPassword"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300"
                >
                  {t('reset.confirmPassword')}
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder={t('repeatNewPassword')}
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm placeholder-slate-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                />
              </div>

              <button
                type="submit"
                disabled={!canSubmit || resetPassword.isPending}
                className="flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {resetPassword.isPending ? t('reset.updating') : t('reset.submit')}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
