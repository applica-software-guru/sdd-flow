import type admin from './locales/en/admin.json';
import type audit from './locales/en/audit.json';
import type auth from './locales/en/auth.json';
import type bugs from './locales/en/bugs.json';
import type changeRequests from './locales/en/change-requests.json';
import type common from './locales/en/common.json';
import type docs from './locales/en/docs.json';
import type errors from './locales/en/errors.json';
import type landing from './locales/en/landing.json';
import type navigation from './locales/en/navigation.json';
import type notifications from './locales/en/notifications.json';
import type profile from './locales/en/profile.json';
import type projects from './locales/en/projects.json';
import type tenants from './locales/en/tenants.json';
import type workers from './locales/en/workers.json';

declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common';
    resources: {
      admin: typeof admin;
      audit: typeof audit;
      auth: typeof auth;
      bugs: typeof bugs;
      'change-requests': typeof changeRequests;
      common: typeof common;
      docs: typeof docs;
      errors: typeof errors;
      landing: typeof landing;
      navigation: typeof navigation;
      notifications: typeof notifications;
      profile: typeof profile;
      projects: typeof projects;
      tenants: typeof tenants;
      workers: typeof workers;
    };
  }
}
