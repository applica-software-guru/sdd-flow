import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSlug from 'rehype-slug';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from '../context/ThemeContext';

interface MarkdownRendererProps {
  content: string;
}

function isExternalLink(href: string) {
  return /^(https?:)?\/\//.test(href);
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const { resolvedTheme } = useTheme();
  const syntaxTheme = resolvedTheme === 'dark' ? oneDark : oneLight;

  const components: Components = {
    a({ href, children, node: _node, ...props }) {
      const target = href && isExternalLink(href) ? '_blank' : undefined;
      const rel = target ? 'noreferrer noopener' : undefined;

      return (
        <a href={href} target={target} rel={rel} {...props}>
          {children}
        </a>
      );
    },
    code({ children, className, node: _node, ...props }) {
      const match = /language-([\w-]+)/.exec(className || '');
      const code = String(children).replace(/\n$/, '');

      if (match) {
        return (
          <div className="markdown-code-block" data-language={match[1]}>
            <SyntaxHighlighter
              PreTag="div"
              language={match[1]}
              style={syntaxTheme}
              customStyle={{
                margin: 0,
                background: 'transparent',
                fontSize: '0.875rem',
                lineHeight: 1.7,
              }}
              codeTagProps={{
                style: {
                  fontFamily: 'inherit',
                },
              }}
            >
              {code}
            </SyntaxHighlighter>
          </div>
        );
      }

      if (code.includes('\n')) {
        return (
          <pre className="markdown-code-block">
            <code className={className} {...props}>
              {code}
            </code>
          </pre>
        );
      }

      return (
        <code className={[className, 'markdown-inline-code'].filter(Boolean).join(' ')} {...props}>
          {children}
        </code>
      );
    },
    table({ children, node: _node, ...props }) {
      return (
        <div className="markdown-table-wrap">
          <table {...props}>{children}</table>
        </div>
      );
    },
  };

  return (
    <div className="markdown-viewer">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[
          rehypeSlug,
          [rehypeAutolinkHeadings, { behavior: 'wrap', properties: { className: ['markdown-heading-link'] } }],
        ]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
