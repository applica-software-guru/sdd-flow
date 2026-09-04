import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import CommentHeader from '../components/CommentHeader';
import AssignmentPanel, { AssignmentHistory } from '../components/AssignmentPanel';
import type { AssignmentHistoryEntry, Comment } from '../types';

describe('CommentHeader', () => {
  const baseComment: Comment = {
    id: 'c1',
    body: 'hello',
    author_id: 'u1',
    author: { id: 'u1', email: 'jane@example.com', display_name: 'Jane Doe', email_verified: true, created_at: '2026-09-04T00:00:00Z' },
    entity_type: 'bug',
    entity_id: 'e1',
    created_at: '2026-09-04T11:59:49Z',
    updated_at: '2026-09-04T11:59:49Z',
  };

  it('renders the author initials, display name and a timestamp with time', () => {
    const markup = renderToStaticMarkup(<CommentHeader comment={baseComment} />);
    expect(markup).toContain('>JD<'); // Jane Doe initials
    expect(markup).toContain('Jane Doe');
    // toLocaleString includes a time component (e.g. AM/PM or 24h), not just a date.
    expect(markup).toMatch(/\d{1,2}:\d{2}/);
  });

  it('falls back to "?" and "Unknown" when no author is resolved', () => {
    const comment = { ...baseComment, author: undefined as unknown as Comment['author'] };
    const markup = renderToStaticMarkup(<CommentHeader comment={comment} />);
    expect(markup).toContain('>?<');
    expect(markup).toContain('Unknown');
  });
});

describe('AssignmentPanel', () => {
  const members = [
    { user_id: 'u1', display_name: 'Jane Doe' },
    { user_id: 'u2', display_name: 'John Smith' },
  ];

  it('renders Author, Assignee and Assign to labels inline (no standalone card shell)', () => {
    const markup = renderToStaticMarkup(
      <AssignmentPanel
        author={{ id: 'u1', display_name: 'Jane Doe', email: 'jane@example.com' }}
        assigneeId="u2"
        members={members}
        onAssign={() => {}}
        assigning={false}
      />
    );
    expect(markup).toContain('Author');
    expect(markup).toContain('Assignee');
    expect(markup).toContain('Assign to');
    expect(markup).toContain('John Smith');
    // No standalone card border / bottom margin wrapper.
    expect(markup).not.toContain('mb-6 rounded-lg border');
  });

  it('does not loop infinitely when the item is unassigned (assigneeId null)', () => {
    // Regression: comparing '' !== null during the render-time state reset
    // used to trigger "Too many re-renders" (CR bug fix).
    const markup = renderToStaticMarkup(
      <AssignmentPanel
        author={{ id: 'u1', display_name: 'Jane Doe', email: 'jane@example.com' }}
        assigneeId={null}
        members={members}
        onAssign={() => {}}
        assigning={false}
      />
    );
    expect(markup).toContain('Unassigned');
  });
});

describe('AssignmentHistory', () => {
  it('renders the history when present and nothing when empty', () => {
    const history: AssignmentHistoryEntry[] = [
      {
        id: 'h1',
        assignee_id: 'u2',
        assignee: { id: 'u2', display_name: 'John Smith', email: 'john@example.com' },
        assigned_by: 'u1',
        assigned_by_name: 'Jane Doe',
        created_at: '2026-09-04T11:59:49Z',
      },
    ];
    const markup = renderToStaticMarkup(
      <AssignmentHistory history={history} entityLabel="Some entity" />
    );
    expect(markup).toContain('Assignment history (1)');
    expect(markup).toContain('assigned to John Smith');

    const empty = renderToStaticMarkup(<AssignmentHistory history={[]} entityLabel="e" />);
    expect(empty).toBe('');
  });
});
