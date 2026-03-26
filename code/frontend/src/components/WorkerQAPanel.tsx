import { useState } from 'react';
import type { WorkerJobMessage } from '../types';

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
    <div className="rounded-lg border border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-900/20 p-4 mt-4">
      <div className="text-sm font-medium text-amber-800 dark:text-amber-300 mb-2">
        Agent is waiting for your response:
      </div>
      <div className="text-sm text-amber-700 dark:text-amber-400 mb-3 font-mono">
        {lastQuestion.content}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Type your answer..."
          className="flex-1 rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          disabled={isSubmitting}
        />
        <button
          type="submit"
          disabled={!answer.trim() || isSubmitting}
          className="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
