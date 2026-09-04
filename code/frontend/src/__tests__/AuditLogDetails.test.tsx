import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { DetailsCell, describeAction, humanizeKey } from '../components/AuditDetailsCell';
import type { AuditLogEntry } from '../types';

function makeEntry(overrides: Partial<AuditLogEntry> = {}): AuditLogEntry {
  return {
    id: '00000000-0000-0000-0000-000000000001',
    tenant_id: '00000000-0000-0000-0000-000000000002',
    user_id: null,
    user: null,
    event_type: 'test.event',
    action: 'test.event',
    entity_type: null,
    entity_id: null,
    entity_label: null,
    summary: null,
    details: {},
    created_at: '2026-04-01T00:00:00Z',
    ...overrides,
  };
}

describe('AuditLogPage DetailsCell', () => {
  it('humanizes known detail keys', () => {
    expect(humanizeKey('new_status')).toBe('New status');
    expect(humanizeKey('old_status')).toBe('Previous status');
    expect(humanizeKey('deleted_bugs')).toBe('Bugs deleted');
  });

  it('falls back to humanizing unknown keys', () => {
    expect(humanizeKey('some_unknown_key')).toBe('Some unknown key');
  });

  it('derives a readable description for legacy entries without summary', () => {
    expect(describeAction('bug.created')).toBe('Created');
    expect(describeAction('cr.transitioned')).toBe('Status changed');
    expect(describeAction('project.reset')).toBe('Data reset');
    expect(describeAction('doc.bulk_upsert')).toBe('Bulk upsert');
  });

  it('renders summary plus friendly key/value chips for primitive payloads', () => {
    const markup = renderToStaticMarkup(
      <DetailsCell
        entry={makeEntry({
          summary: 'status: new → open',
          details: { old_status: 'new', new_status: 'open' },
        })}
      />
    );
    expect(markup).toContain('status: new → open');
    expect(markup).toContain('Previous status');
    expect(markup).toContain('New status');
    expect(markup).not.toContain('{');
  });

  it('renders chips without summary when only details exist', () => {
    const markup = renderToStaticMarkup(
      <DetailsCell entry={makeEntry({ details: { created: 2, updated: 0 } })} />
    );
    expect(markup).toContain('Created');
    expect(markup).toContain('Updated');
    expect(markup).toContain('>2<');
  });

  it('falls back to raw JSON for complex payloads (BUG-005 treatment)', () => {
    const markup = renderToStaticMarkup(
      <DetailsCell
        entry={makeEntry({ details: { nested: { a: 1 } } })}
      />
    );
    expect(markup).toContain('font-mono');
    expect(markup).toContain('&quot;nested&quot;');
  });

  it('renders a derived description for legacy entries instead of an empty cell', () => {
    const markup = renderToStaticMarkup(
      <DetailsCell entry={makeEntry({ action: 'api_key.created' })} />
    );
    expect(markup).toContain('Created');
    expect(markup).not.toContain('--');
  });
});
