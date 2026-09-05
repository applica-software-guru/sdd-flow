import i18next from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';
import adminEn from './locales/en/admin.json';
import auditEn from './locales/en/audit.json';
import authEn from './locales/en/auth.json';
import bugsEn from './locales/en/bugs.json';
import changeRequestsEn from './locales/en/change-requests.json';
import commonEn from './locales/en/common.json';
import docsEn from './locales/en/docs.json';
import errorsEn from './locales/en/errors.json';
import landingEn from './locales/en/landing.json';
import navigationEn from './locales/en/navigation.json';
import notificationsEn from './locales/en/notifications.json';
import profileEn from './locales/en/profile.json';
import projectsEn from './locales/en/projects.json';
import tenantsEn from './locales/en/tenants.json';
import workersEn from './locales/en/workers.json';
import adminIt from './locales/it/admin.json';
import auditIt from './locales/it/audit.json';
import authIt from './locales/it/auth.json';
import bugsIt from './locales/it/bugs.json';
import changeRequestsIt from './locales/it/change-requests.json';
import commonIt from './locales/it/common.json';
import docsIt from './locales/it/docs.json';
import errorsIt from './locales/it/errors.json';
import landingIt from './locales/it/landing.json';
import navigationIt from './locales/it/navigation.json';
import notificationsIt from './locales/it/notifications.json';
import profileIt from './locales/it/profile.json';
import projectsIt from './locales/it/projects.json';
import tenantsIt from './locales/it/tenants.json';
import workersIt from './locales/it/workers.json';

export const supportedLanguages = ['en', 'it'] as const;
export type SupportedLanguage = (typeof supportedLanguages)[number];
export const LANGUAGE_STORAGE_KEY = 'sdd-flow-language';

const resources = {
  en: {
    admin: adminEn,
    audit: auditEn,
    auth: authEn,
    bugs: bugsEn,
    'change-requests': changeRequestsEn,
    common: commonEn,
    docs: docsEn,
    errors: errorsEn,
    landing: landingEn,
    navigation: navigationEn,
    notifications: notificationsEn,
    profile: profileEn,
    projects: projectsEn,
    tenants: tenantsEn,
    workers: workersEn,
  },
  it: {
    admin: adminIt,
    audit: auditIt,
    auth: authIt,
    bugs: bugsIt,
    'change-requests': changeRequestsIt,
    common: commonIt,
    docs: docsIt,
    errors: errorsIt,
    landing: landingIt,
    navigation: navigationIt,
    notifications: notificationsIt,
    profile: profileIt,
    projects: projectsIt,
    tenants: tenantsIt,
    workers: workersIt,
  },
} as const;

function normalizedLanguage(language?: string): SupportedLanguage {
  return language?.toLowerCase().split('-')[0] === 'it' ? 'it' : 'en';
}

function syncDocumentLanguage(language?: string) {
  if (typeof document !== 'undefined') document.documentElement.lang = normalizedLanguage(language);
}

void i18next
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    supportedLngs: supportedLanguages,
    nonExplicitSupportedLngs: true,
    fallbackLng: 'en',
    defaultNS: 'common',
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: LANGUAGE_STORAGE_KEY,
      caches: ['localStorage'],
    },
    interpolation: { escapeValue: false },
    debug: import.meta.env.DEV && import.meta.env.MODE !== 'test',
  })
  .then(() => syncDocumentLanguage(i18next.resolvedLanguage));

i18next.on('languageChanged', syncDocumentLanguage);

export function translate(key: string, options?: Record<string, unknown>): string {
  return String(i18next.t(key as never, options as never));
}

export { normalizedLanguage };
export default i18next;
