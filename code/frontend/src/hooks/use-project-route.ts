import { useParams } from 'react-router-dom';

export function useProjectRoute() {
  const { tenantId, projectId } = useParams();
  return tenantId && projectId ? { tenantId, projectId } : null;
}
