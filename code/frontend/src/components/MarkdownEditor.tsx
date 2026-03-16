import MDEditor from '@uiw/react-md-editor';
import { useTheme } from '../context/ThemeContext';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: number;
}

export default function MarkdownEditor({
  value,
  onChange,
  height = 300,
}: MarkdownEditorProps) {
  const { resolvedTheme } = useTheme();

  return (
    <div data-color-mode={resolvedTheme} className="mt-1 md-editor-custom">
      <MDEditor
        value={value}
        onChange={(val) => onChange(val ?? '')}
        height={height}
        preview="edit"
      />
    </div>
  );
}
