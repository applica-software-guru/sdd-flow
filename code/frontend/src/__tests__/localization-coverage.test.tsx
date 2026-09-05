import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, describe, expect, it } from 'vitest';
import JobStatusBadge from '@/components/job-status-badge';
import SeverityBadge from '@/components/severity-badge';
import StatusBadge from '@/components/status-badge';
import WorkerStatusBadge from '@/components/worker-status-badge';
import i18n from '@/i18n';
import { describeAction, humanizeKey } from '@/lib/audit-details';

describe('localized domain labels', () => {
  afterEach(async () => {
    await i18n.changeLanguage('en');
  });

  it('renders status, severity and worker labels in Italian without changing raw values', async () => {
    await i18n.changeLanguage('it');

    expect(renderToStaticMarkup(<StatusBadge status="in_progress" />)).toContain('In corso');
    expect(renderToStaticMarkup(<SeverityBadge severity="critical" />)).toContain('Critica');
    expect(renderToStaticMarkup(<JobStatusBadge status="queued" />)).toContain('In coda');
    expect(renderToStaticMarkup(<WorkerStatusBadge status="busy" />)).toContain('Occupato');
  });

  it('localizes known audit keys and actions while preserving unknown fallbacks', async () => {
    await i18n.changeLanguage('it');

    expect(humanizeKey('old_status')).toBe('Stato precedente');
    expect(describeAction('bug.transitioned')).toBe('Stato modificato');
    expect(humanizeKey('custom_field')).toBe('Custom field');
  });
});
