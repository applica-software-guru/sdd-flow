import MDEditor from '@uiw/react-md-editor';

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
  return (
    <div data-color-mode="light" className="mt-1">
      <MDEditor
        value={value}
        onChange={(val) => onChange(val ?? '')}
        height={height}
        preview="live"
      />
    </div>
  );
}
