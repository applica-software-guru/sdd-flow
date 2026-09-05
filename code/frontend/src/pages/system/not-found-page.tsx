import { Link } from 'react-router-dom';
import { translate } from '@/i18n';

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="text-center">
        <p className="text-6xl font-bold text-blue-600 dark:text-blue-400">404</p>
        <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-slate-100">
          {translate('common:auto.page_not_found')}
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {translate('common:auto.the_page_you_are_looking_for_does')}
        </p>
        <div className="mt-8">
          <Link
            to="/tenants"
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
              />
            </svg>
            {translate('common:auto.go_to_dashboard')}
          </Link>
        </div>
      </div>
    </div>
  );
}
