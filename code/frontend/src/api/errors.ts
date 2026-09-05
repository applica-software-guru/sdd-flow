interface ApiErrorBody {
  detail?: string;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (typeof error !== 'object' || error === null || !('response' in error)) return fallback;
  const response = error.response;
  if (typeof response !== 'object' || response === null || !('data' in response)) return fallback;
  const data = response.data as ApiErrorBody | undefined;
  return typeof data?.detail === 'string' && data.detail.trim() ? data.detail : fallback;
}
