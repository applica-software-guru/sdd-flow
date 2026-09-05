import { useEffect, useRef } from 'react';
import type { WorkerJobMessage } from '../types';
import MarkdownRenderer from './markdown-renderer';
import { translate } from '@/i18n';

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
    <div className="max-h-[600px] min-h-[200px] overflow-auto rounded-lg border border-slate-200 bg-slate-100 dark:border-slate-700 dark:bg-slate-800">
      {messages.length === 0 && isStreaming && (
        <div className="animate-pulse p-4 font-mono text-sm text-slate-500">
          {translate('workers:auto.waiting_for_output')}
        </div>
      )}
      {messages.map((msg) => {
        if (msg.kind === 'output') {
          return (
            <div
              key={msg.id}
              className="border-b border-slate-100 px-5 py-3 last:border-b-0 dark:border-slate-800"
            >
              <MarkdownRenderer content={msg.content} />
            </div>
          );
        }

        return (
          <div
            key={msg.id}
            className={`whitespace-pre-wrap break-words border-b border-slate-100 px-4 py-2 font-mono text-sm last:border-b-0 dark:border-slate-800 ${
              msg.kind === 'question'
                ? 'bg-amber-50 text-amber-800 dark:bg-amber-950/30 dark:text-amber-300'
                : 'bg-green-50 text-green-800 dark:bg-green-950/30 dark:text-green-300'
            }`}
          >
            <span className="mr-2 font-semibold">{msg.kind === 'question' ? '[?]' : '[A]'}</span>
            {msg.content}
          </div>
        );
      })}
      {isStreaming && (
        <div className="px-4 py-2">
          <span className="inline-block h-4 w-2 animate-pulse bg-slate-400" />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
