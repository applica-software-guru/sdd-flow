import { describe, expect, it } from 'vitest';
import { createRef } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ScrollToCommentsButton from '../components/scroll-to-comments-button';

describe('ScrollToCommentsButton', () => {
  it('renders an accessible button with a comment count badge', () => {
    const markup = renderToStaticMarkup(
      <ScrollToCommentsButton targetRef={createRef<HTMLDivElement>()} commentCount={3} />
    );
    expect(markup).toContain('aria-label="Scroll to comments"');
    expect(markup).toContain('>3<');
    expect(markup).toContain('Comments');
  });

  it('starts hidden until the observer reports the comments below the fold', () => {
    const markup = renderToStaticMarkup(
      <ScrollToCommentsButton targetRef={createRef<HTMLDivElement>()} commentCount={0} />
    );
    // Initial state: invisible (fades in via IntersectionObserver effect).
    expect(markup).toContain('opacity-0');
    expect(markup).not.toContain('opacity-100');
  });

  it('renders nothing without a comment count', () => {
    const markup = renderToStaticMarkup(
      <ScrollToCommentsButton
        targetRef={createRef<HTMLDivElement>()}
        commentCount={undefined as unknown as number}
      />
    );
    expect(markup).toBe('');
  });
});
