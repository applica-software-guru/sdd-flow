import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { useTheme } from '../context/theme';

let idCounter = 0;

interface MermaidBlockProps {
  chart: string;
}

export default function MermaidBlock({ chart }: MermaidBlockProps) {
  const { resolvedTheme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    let cancelled = false;

    mermaid.initialize({
      startOnLoad: false,
      theme: resolvedTheme === 'dark' ? 'dark' : 'default',
    });

    const id = `mermaid-${++idCounter}`;

    mermaid.render(id, chart).then(({ svg }) => {
      if (!cancelled && containerRef.current) {
        containerRef.current.innerHTML = svg;
        setError(null);
      }
    }).catch((err) => {
      if (!cancelled) setError(String(err));
    });

    return () => { cancelled = true; };
  }, [chart, resolvedTheme]);

  if (error) {
    return <pre className="markdown-code-block text-red-500">{chart}</pre>;
  }

  return <div ref={containerRef} className="mermaid-diagram my-4" />;
}
