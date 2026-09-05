import { useEffect, useRef, useState } from 'react';
import {
  useWorkers,
  useAgentModels,
  usePreviewJobPrompt,
  useCreateWorkerJob,
} from '../hooks/use-workers';
import type { JobType } from '../types';
import { Dialog, DialogContent, DialogDescription, DialogTitle } from './ui/dialog';

interface Props {
  tenantId: string;
  projectId: string;
  jobType: JobType;
  entityType?: 'change_request' | 'bug' | 'document';
  entityId?: string;
  onSuccess: (jobId: string) => void;
  onCancel: () => void;
}

const JOB_TYPE_LABELS: Record<JobType, string> = {
  enrich: 'Enrich',
  build: 'Build',
  custom: 'Custom Job',
};

export default function JobOptionsDialog({
  tenantId,
  projectId,
  jobType,
  entityType,
  entityId,
  onSuccess,
  onCancel,
}: Props) {
  const { data: workers } = useWorkers(tenantId, projectId);
  const { data: agentModels } = useAgentModels(tenantId, projectId);
  const previewPrompt = usePreviewJobPrompt(tenantId, projectId);
  const createJob = useCreateWorkerJob(tenantId, projectId);

  const isCustom = jobType === 'custom';
  const onlineWorkers = workers?.filter((w) => w.is_online) ?? [];

  const [selectedWorkerId, setSelectedWorkerId] = useState<string>('');
  const [selectedAgent, setSelectedAgent] = useState<string>('claude');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [prompt, setPrompt] = useState<string>('');
  // Custom jobs are always editable; others start locked (preview mode)
  const [editingPrompt, setEditingPrompt] = useState(isCustom);
  const [promptLoaded, setPromptLoaded] = useState(isCustom);

  // Auto-select the only online worker (render-time reset, see
  // "You Might Not Need an Effect": converges because the guard flips).
  if (onlineWorkers.length === 1 && !selectedWorkerId) {
    setSelectedWorkerId(onlineWorkers[0].id);
    setSelectedAgent(onlineWorkers[0].agent);
  }

  // Reset the model whenever the agent or the models list changes
  // (render-time reset, see "You Might Not Need an Effect").
  const [prevModelsKey, setPrevModelsKey] = useState<string | null>(null);
  const modelsKey = `${selectedAgent}:${agentModels ? Object.keys(agentModels).length : -1}`;
  if (prevModelsKey !== modelsKey) {
    setPrevModelsKey(modelsKey);
    const models = agentModels?.[selectedAgent] ?? [];
    setSelectedModel(models[0]?.id ?? '');
  }

  // Load prompt preview once (not for custom jobs)
  const previewRequestedRef = useRef(false);
  useEffect(() => {
    if (promptLoaded || isCustom || previewRequestedRef.current) return;
    previewRequestedRef.current = true;
    previewPrompt.mutate(
      { entity_type: entityType, entity_id: entityId, job_type: jobType },
      {
        onSuccess: (data) => {
          setPrompt(data.prompt);
          setPromptLoaded(true);
        },
      }
    );
  }, [promptLoaded, isCustom, entityType, entityId, jobType, previewPrompt]);

  const handleConfirm = async () => {
    const result = await createJob.mutateAsync({
      entity_type: entityType,
      entity_id: entityId,
      job_type: jobType,
      agent: selectedAgent,
      model: selectedModel || undefined,
      worker_id: selectedWorkerId || undefined,
      // Custom jobs always send the prompt; others only if edited
      prompt: isCustom || editingPrompt ? prompt : undefined,
    });
    onSuccess(result.id);
  };

  const selectedWorker = onlineWorkers.find((w) => w.id === selectedWorkerId);
  const availableModels = agentModels?.[selectedAgent] ?? [];
  const canDispatch =
    !createJob.isPending && onlineWorkers.length > 0 && (!isCustom || prompt.trim().length > 0);

  return (
    <Dialog open onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto p-0">
        <div className="border-b border-slate-200 px-6 py-5 dark:border-slate-700">
          <DialogTitle className="text-lg font-semibold">
            {JOB_TYPE_LABELS[jobType]} on Worker
          </DialogTitle>
          <DialogDescription className={isCustom ? 'mt-1' : 'sr-only'}>
            {isCustom
              ? 'Write any prompt — the worker will execute it as-is.'
              : 'Configure the worker and model used for this job.'}
          </DialogDescription>
        </div>

        <div className="space-y-5 p-6">
          {/* Worker selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Worker
            </label>
            {onlineWorkers.length === 0 ? (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                No workers online. Start a worker with{' '}
                <code className="rounded bg-slate-100 px-1 py-0.5 text-xs dark:bg-slate-700">
                  sdd remote worker
                </code>
              </p>
            ) : (
              <select
                value={selectedWorkerId}
                onChange={(e) => {
                  setSelectedWorkerId(e.target.value);
                  const w = onlineWorkers.find((x) => x.id === e.target.value);
                  if (w) setSelectedAgent(w.agent);
                }}
                className="sdd-select mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              >
                <option value="">Any available worker</option>
                {onlineWorkers.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name} — {w.agent}
                    {w.branch ? ` (branch: ${w.branch})` : ''}
                  </option>
                ))}
              </select>
            )}
            {selectedWorker?.branch && (
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Branch: <code className="font-mono">{selectedWorker.branch}</code>
              </p>
            )}
          </div>

          {/* Model selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="sdd-select mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              disabled={availableModels.length === 0}
            >
              {availableModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          {/* Prompt */}
          <div>
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Prompt
              </label>
              {!isCustom && (
                <button
                  type="button"
                  onClick={() => setEditingPrompt((v) => !v)}
                  className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {editingPrompt ? 'Lock' : 'Edit'}
                </button>
              )}
            </div>
            {!isCustom && previewPrompt.isPending ? (
              <div className="mt-1 flex items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-4 text-sm text-slate-400 dark:border-slate-700 dark:bg-slate-700/30">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                Generating prompt...
              </div>
            ) : (
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                readOnly={!editingPrompt}
                rows={isCustom ? 14 : 10}
                placeholder={isCustom ? 'Enter your prompt here...' : undefined}
                className="mt-1 block w-full rounded-md border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-xs shadow-sm focus:outline-none dark:border-slate-600 dark:bg-slate-700/30 dark:text-slate-200"
                style={{ resize: 'vertical' }}
              />
            )}
            {isCustom && prompt.trim().length === 0 && (
              <p className="mt-1 text-xs text-red-500 dark:text-red-400">Prompt is required.</p>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4 dark:border-slate-700">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!canDispatch}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createJob.isPending ? 'Dispatching...' : 'Dispatch Job'}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
