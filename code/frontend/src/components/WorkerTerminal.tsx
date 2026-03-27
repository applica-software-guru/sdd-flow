import { useEffect, useRef } from 'react';
import type { WorkerJobMessage } from '../types';
import MarkdownRenderer from './MarkdownRenderer';

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
    <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 overflow-auto max-h-[600px] min-h-[200px]">
      {messages.length === 0 && isStreaming && (
        <div className="p-4 text-slate-500 animate-pulse font-mono text-sm">Waiting for output...</div>
      )}
      {messages.map((msg) => {
        if (msg.kind === 'output') {
          return (
            <div key={msg.id} className="px-5 py-3 border-b border-slate-100 dark:border-slate-800 last:border-b-0">
              <MarkdownRenderer content={msg.content} />
            </div>
          );
        }

        return (
          <div
            key={msg.id}
            className={`px-4 py-2 font-mono text-sm whitespace-pre-wrap break-words border-b border-slate-100 dark:border-slate-800 last:border-b-0 ${
              msg.kind === 'question'
                ? 'bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300'
                : 'bg-green-50 dark:bg-green-950/30 text-green-800 dark:text-green-300'
            }`}
          >
            <span className="font-semibold mr-2">{msg.kind === 'question' ? '[?]' : '[A]'}</span>
            {msg.content}
          </div>
        );
      })}
      {isStreaming && (
        <div className="px-4 py-2">
          <span className="inline-block w-2 h-4 bg-slate-400 animate-pulse" />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
