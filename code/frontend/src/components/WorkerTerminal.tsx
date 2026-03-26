import { useEffect, useRef } from 'react';
import type { WorkerJobMessage } from '../types';

const kindStyles: Record<string, string> = {
  output: 'text-slate-300',
  question: 'text-amber-400 font-semibold',
  answer: 'text-green-400',
};

interface WorkerTerminalProps {
  messages: WorkerJobMessage[];
  isStreaming: boolean;
}

export default function WorkerTerminal({ messages, isStreaming }: WorkerTerminalProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  return (
    <div className="rounded-lg bg-slate-900 p-4 font-mono text-sm overflow-auto max-h-[600px] min-h-[200px]">
      {messages.length === 0 && isStreaming && (
        <div className="text-slate-500 animate-pulse">Waiting for output...</div>
      )}
      {messages.map((msg) => (
        <div key={msg.id} className={`whitespace-pre-wrap break-words ${kindStyles[msg.kind] || 'text-slate-300'}`}>
          {msg.kind === 'question' && <span className="text-amber-500 mr-1">[?]</span>}
          {msg.kind === 'answer' && <span className="text-green-500 mr-1">[A]</span>}
          {msg.content}
        </div>
      ))}
      {isStreaming && (
        <div className="mt-1">
          <span className="inline-block w-2 h-4 bg-slate-400 animate-pulse" />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
