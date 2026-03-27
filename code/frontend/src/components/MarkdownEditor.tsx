import type { CSSProperties } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { useTheme } from '../context/ThemeContext';

export const MARKDOWN_EDITOR_FONT_STACK = 'ui-monospace, SFMono-Regular, SF Mono, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: number;
}

export default function MarkdownEditor({
  value,
  onChange,
  height = 400,
}: MarkdownEditorProps) {
  const { resolvedTheme } = useTheme();

  return (
    <div
      data-color-mode={resolvedTheme}
      className="mt-1 md-editor-custom"
      style={{ '--md-editor-font-family': MARKDOWN_EDITOR_FONT_STACK } as CSSProperties}
    >
      <MDEditor
        value={value}
        onChange={(val) => onChange(val ?? '')}
        height={height}
        preview="edit"
      />
    </div>
  );
}
