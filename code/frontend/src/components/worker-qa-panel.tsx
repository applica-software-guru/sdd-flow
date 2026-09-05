import { useState } from 'react';
import type { WorkerJobMessage } from '../types';
import { translate } from '@/i18n';

interface WorkerQAPanelProps {
  messages: WorkerJobMessage[];
  onAnswer: (content: string) => void;
  isSubmitting: boolean;
}

export default function WorkerQAPanel({ messages, onAnswer, isSubmitting }: WorkerQAPanelProps) {
  const [answer, setAnswer] = useState('');

  // Find the latest unanswered question
  const lastQuestion = [...messages].reverse().find((m) => m.kind === 'question');
  const lastAnswer = [...messages].reverse().find((m) => m.kind === 'answer');

  // Show panel only if there's a question that hasn't been answered
  const hasPendingQuestion =
    lastQuestion && (!lastAnswer || lastAnswer.sequence < lastQuestion.sequence);

  if (!hasPendingQuestion || !lastQuestion) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim()) {
      onAnswer(answer.trim());
      setAnswer('');
    }
  };

  return (
    <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-900/20">
      <div className="mb-2 text-sm font-medium text-amber-800 dark:text-amber-300">
        {translate('workers:auto.agent_is_waiting_for_your_response')}
      </div>
      <div className="mb-3 font-mono text-sm text-amber-700 dark:text-amber-400">
        {lastQuestion.content}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder={translate('workers:auto.type_your_answer')}
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 dark:border-slate-600 dark:bg-slate-800"
          disabled={isSubmitting}
        />
        <button
          type="submit"
          disabled={!answer.trim() || isSubmitting}
          className="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
        >
          {isSubmitting ? translate('workers:auto.sending') : translate('workers:auto.send')}
        </button>
      </form>
    </div>
  );
}
