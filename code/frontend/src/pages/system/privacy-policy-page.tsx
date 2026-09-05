import { Link } from 'react-router-dom';
import LandingNavbar from '../../components/landing/landing-navbar';
import { translate } from '@/i18n';

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-900">
      <LandingNavbar />

      <main className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          {translate('common:auto.privacy_policy')}
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {translate('common:auto.last_updated_april_19_2026')}
        </p>

        <div className="mt-10 space-y-10 text-slate-700 dark:text-slate-300">
          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.1_who_we_are')}
            </h2>
            <p className="mt-3 text-sm leading-relaxed">
              {translate('common:auto.sdd_flow_is_operated_by')}
              <strong>{translate('common:auto.applica_software_guru')}</strong> (
              <a
                href="mailto:bruno.fortunato@applica.guru"
                className="text-blue-600 hover:underline dark:text-blue-400"
              >
                {translate('common:auto.bruno_fortunato_applica_guru')}
              </a>
              {translate('common:auto.this_policy_explains_what_data_we_collect')}
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.2_data_we_collect')}
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
              <li>
                <strong>{translate('common:auto.account_data')}</strong>
                {translate('common:auto.email_address_name_and_hashed_password_when')}
              </li>
              <li>
                <strong>{translate('common:auto.project_data')}</strong>
                {translate('common:auto.sdd_documentation_files_docs_change_requests_bugs')}
              </li>
              <li>
                <strong>{translate('common:auto.usage_data')}</strong>
                {translate('common:auto.basic_server_logs_ip_address_timestamps_http')}
              </li>
              <li>
                <strong>{translate('common:auto.authentication_tokens')}</strong>
                {translate('common:auto.short_lived_jwt_access_tokens_and_7')}
              </li>
            </ul>
            <p className="mt-3 text-sm leading-relaxed">
              {translate('common:auto.we_do_not_collect_payment_information_run')}
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.3_how_we_use_your_data')}
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
              <li>{translate('common:auto.to_provide_and_operate_the_sdd_flow')}</li>
              <li>{translate('common:auto.to_authenticate_you_and_keep_your_session')}</li>
              <li>{translate('common:auto.to_store_and_sync_your_sdd_project')}</li>
              <li>{translate('common:auto.to_dispatch_ai_agent_jobs_to_your')}</li>
              <li>
                {translate('common:auto.to_send_transactional_emails_password_reset_invitations')}
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.4_data_storage_and_security')}
            </h2>
            <p className="mt-3 text-sm leading-relaxed">
              {translate('common:auto.data_is_stored_in_a_postgresql_database')}
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.5_data_retention')}
            </h2>
            <p className="mt-3 text-sm leading-relaxed">
              {translate('common:auto.your_data_is_retained_as_long_as')}
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.6_third_party_services')}
            </h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
              <li>
                <strong>{translate('common:auto.google_oauth')}</strong>
                {translate('common:auto.if_you_sign_in_with_google_we')}
              </li>
              <li>
                <strong>{translate('common:auto.google_cloud')}</strong>
                {translate('common:auto.infrastructure_provider_for_hosting_and_database')}
              </li>
              <li>
                <strong>{translate('common:auto.cloudflare_pages')}</strong>
                {translate('common:auto.cdn_and_hosting_for_the_frontend')}
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.7_your_rights')}
            </h2>
            <p className="mt-3 text-sm leading-relaxed">
              {translate('common:auto.you_have_the_right_to_access_correct')}{' '}
              <a
                href="mailto:bruno.fortunato@applica.guru"
                className="text-blue-600 hover:underline dark:text-blue-400"
              >
                {translate('common:auto.bruno_fortunato_applica_guru')}
              </a>
              {translate('common:auto.we_will_respond_within_30_days')}
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.8_cookies')}
            </h2>
            <p className="mt-3 text-sm leading-relaxed">
              {translate('common:auto.we_use_http_only_cookies_solely_for')}
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.9_changes_to_this_policy')}
            </h2>
            <p className="mt-3 text-sm leading-relaxed">
              {translate('common:auto.we_may_update_this_policy_from_time')}
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {translate('common:auto.10_contact')}
            </h2>
            <p className="mt-3 text-sm leading-relaxed">
              {translate('common:auto.for_any_privacy_related_questions_contact')}{' '}
              <a
                href="mailto:bruno.fortunato@applica.guru"
                className="text-blue-600 hover:underline dark:text-blue-400"
              >
                {translate('common:auto.bruno_fortunato_applica_guru')}
              </a>
            </p>
          </section>
        </div>

        <div className="mt-16 border-t border-slate-200 pt-8 dark:border-slate-700">
          <Link to="/" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
            {translate('common:auto.back_to_home')}
          </Link>
        </div>
      </main>
    </div>
  );
}
