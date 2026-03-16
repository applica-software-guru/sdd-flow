import { Navigate, useParams } from 'react-router-dom';

export default function ProjectListPage() {
  const { tenantId } = useParams();
  return <Navigate to={`/tenants/${tenantId}`} replace />;
}
