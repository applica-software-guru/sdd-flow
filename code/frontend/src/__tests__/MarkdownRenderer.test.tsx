import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import MarkdownRenderer from '../components/MarkdownRenderer';

vi.mock('react-syntax-highlighter', () => ({
  Prism: ({ children }: { children: string }) => <pre>{children}</pre>,
}));

vi.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
  oneDark: {},
  oneLight: {},
}));

vi.mock('../context/ThemeContext', () => ({
  useTheme: () => ({
    resolvedTheme: 'light',
  }),
}));

describe('MarkdownRenderer', () => {
  it('renders GFM tables, task lists, and heading anchors', () => {
    const markup = renderToStaticMarkup(
      <MarkdownRenderer
        content={`# Release Notes

| Name | Value |
| --- | --- |
| docs | ready |

- [x] shipped
- [ ] verify`}
      />
    );

    expect(markup).toContain('<table');
    expect(markup).toContain('type="checkbox"');
    expect(markup).toContain('href="#release-notes"');
  });

  it('renders fenced code blocks with language metadata', () => {
    const markup = renderToStaticMarkup(
      <MarkdownRenderer content={"```ts\nconst answer = 42;\n```"} />
    );

    expect(markup).toContain('class="markdown-code-block"');
    expect(markup).toContain('data-language="ts"');
    expect(markup).toContain('const');
  });

  it('opens external links in a new tab', () => {
    const markup = renderToStaticMarkup(
      <MarkdownRenderer content={'[External](https://example.com)'} />
    );

    expect(markup).toContain('target="_blank"');
    expect(markup).toContain('rel="noreferrer noopener"');
  });

  it('keeps raw HTML escaped by default', () => {
    const markup = renderToStaticMarkup(
      <MarkdownRenderer content={'<script>alert(1)</script>'} />
    );

    expect(markup).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
  });
});