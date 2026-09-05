import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '@/components/language-selector';
import { useForgotPassword } from '../../hooks/use-auth';
import { getApiErrorMessage } from '../../api/errors';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const forgotPassword = useForgotPassword();
  const { t } = useTranslation('auth');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await forgotPassword.mutateAsync({ email });
      setSubmitted(true);
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
            {t('forgot.title')}
          </h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{t('forgot.subtitle')}</p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          {submitted ? (
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-900/30 dark:text-green-400">
              {t('forgot.success')}
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {forgotPassword.isError && (
                <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400">
                  {getApiErrorMessage(forgotPassword.error, t('forgot.failed'))}
                </div>
              )}

              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300"
                >
                  {t('email')}
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('emailPlaceholder')}
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm placeholder-slate-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                />
              </div>

              <button
                type="submit"
                disabled={forgotPassword.isPending}
                className="flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {forgotPassword.isPending ? t('forgot.submitting') : t('forgot.submit')}
              </button>
            </form>
          )}
        </div>

        <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
          {t('forgot.backTo')}{' '}
          <Link
            to="/login"
            className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400"
          >
            {t('login.submit')}
          </Link>
        </p>
      </div>
    </div>
  );
}
