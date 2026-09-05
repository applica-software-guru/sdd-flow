import { useEffect, useRef, useState } from 'react';
import { queryKeys } from '../api/query-keys';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';
import { useToast } from '../context/toast';
import type {
  Worker,
  WorkerJob,
  WorkerJobDetail,
  WorkerJobMessage,
  PaginatedResponse,
  AgentModel,
} from '../types';

// --- Workers ---

export function useWorkers(tenantId: string | undefined, projectId: string | undefined) {
  return useQuery<Worker[]>({
    queryKey: queryKeys.workers.all(tenantId, projectId),
    queryFn: async () => {
      const { data } = await api.get(`/tenants/${tenantId}/projects/${projectId}/workers`);
      return data;
    },
    enabled: !!tenantId && !!projectId,
    refetchInterval: 15_000,
  });
}

// --- Worker Jobs ---

interface JobFilters {
  status?: string;
  page?: number;
  page_size?: number;
}

export function useWorkerJobs(
  tenantId: string | undefined,
  projectId: string | undefined,
  filters?: JobFilters
) {
  return useQuery<PaginatedResponse<WorkerJob>>({
    queryKey: queryKeys.workers.jobList(tenantId, projectId, filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set('status', filters.status);
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.page_size) params.set('page_size', String(filters.page_size));
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/worker-jobs?${params}`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId,
  });
}

const LIVE_JOB_STATUSES = new Set(['queued', 'assigned', 'running']);

export function useWorkerJob(
  tenantId: string | undefined,
  projectId: string | undefined,
  jobId: string | undefined
) {
  return useQuery<WorkerJobDetail>({
    queryKey: queryKeys.workers.job(tenantId, projectId, jobId),
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/worker-jobs/${jobId}`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId && !!jobId,
    refetchInterval: (query) =>
      query.state.data && LIVE_JOB_STATUSES.has(query.state.data.status) ? 3000 : false,
  });
}

export interface CreateWorkerJobPayload {
  entity_type?: 'change_request' | 'bug' | 'document';
  entity_id?: string;
  job_type?: 'enrich' | 'build' | 'custom';
  agent?: string;
  model?: string;
  prompt?: string;
  worker_id?: string;
}

export function useCreateWorkerJob(tenantId: string, projectId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async (payload: CreateWorkerJobPayload) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/worker-jobs`,
        payload
      );
      return data as WorkerJob;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.workers.jobs(tenantId, projectId),
      });
      addToast('Job dispatched to worker', 'success');
    },
    onError: () => {
      addToast('Failed to dispatch job', 'error');
    },
  });
}

export function useAgentModels(tenantId: string | undefined, projectId: string | undefined) {
  return useQuery<Record<string, AgentModel[]>>({
    queryKey: queryKeys.workers.models(tenantId, projectId),
    queryFn: async () => {
      const { data } = await api.get(
        `/tenants/${tenantId}/projects/${projectId}/worker-jobs/agent-models`
      );
      return data;
    },
    enabled: !!tenantId && !!projectId,
    staleTime: Infinity, // static config, never stale
  });
}

export function usePreviewJobPrompt(tenantId: string, projectId: string) {
  return useMutation({
    mutationFn: async (payload: { entity_type?: string; entity_id?: string; job_type: string }) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/worker-jobs/preview`,
        payload
      );
      return data as { prompt: string };
    },
  });
}

export function useAnswerQuestion(tenantId: string, projectId: string, jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (content: string) => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/worker-jobs/${jobId}/answer`,
        { content }
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.workers.job(tenantId, projectId, jobId),
      });
    },
  });
}

export function useCancelJob(tenantId: string, projectId: string, jobId: string) {
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(
        `/tenants/${tenantId}/projects/${projectId}/worker-jobs/${jobId}/cancel`
      );
      return data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.workers.jobs(tenantId, projectId),
      });
      addToast('Job cancelled', 'success');
    },
    onError: () => {
      addToast('Failed to cancel job', 'error');
    },
  });
}

// --- SSE Stream hook ---

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || '/api/v1';

export function useWorkerJobStream(
  tenantId: string | undefined,
  projectId: string | undefined,
  jobId: string | undefined,
  enabled: boolean = true,
  onDone?: () => void
) {
  const [messages, setMessages] = useState<WorkerJobMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(true);
  const [jobResult, setJobResult] = useState<{ status: string; exit_code?: number } | null>(null);

  // Reset the stream state when the target job changes
  // (render-time reset, see "You Might Not Need an Effect").
  const streamKey =
    tenantId && projectId && jobId && enabled ? `${tenantId}:${projectId}:${jobId}` : null;
  const [prevStreamKey, setPrevStreamKey] = useState<string | null>(null);
  if (prevStreamKey !== streamKey) {
    setPrevStreamKey(streamKey);
    setMessages([]);
    setIsStreaming(true);
    setJobResult(null);
  }

  // Keep the latest onDone callback without re-subscribing the stream.
  const onDoneRef = useRef(onDone);
  useEffect(() => {
    onDoneRef.current = onDone;
  });

  useEffect(() => {
    if (!tenantId || !projectId || !jobId || !enabled) return;

    const url = `${API_BASE_URL}/tenants/${tenantId}/projects/${projectId}/worker-jobs/${jobId}/stream`;
    const eventSource = new EventSource(url, { withCredentials: true });

    eventSource.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WorkerJobMessage;
        setMessages((prev) => [...prev, msg]);
      } catch {
        // ignore parse errors
      }
    };

    eventSource.addEventListener('done', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data);
        setJobResult(data);
      } catch {
        // ignore
      }
      setIsStreaming(false);
      eventSource.close();
      onDoneRef.current?.();
    });

    eventSource.onerror = () => {
      setIsStreaming(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [tenantId, projectId, jobId, enabled]);

  return { messages, isStreaming, jobResult };
}
